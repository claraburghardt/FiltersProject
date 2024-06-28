import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from PIL import Image, ImageTk
import cv2 as cv
import numpy as np
import os
from filters import apply_filter

# Function to load images with an alpha channel
def load_image_with_alpha(filepath):
    image = cv.imread(filepath, cv.IMREAD_UNCHANGED)
    if image is None:
        return None
    if image.shape[2] == 3:
        # Add an alpha channel if it doesn't exist
        b, g, r = cv.split(image)
        alpha = np.ones(b.shape, dtype=b.dtype) * 255
        image = cv.merge([b, g, r, alpha])
    return image

# Path to the folder where stickers are stored
stickers_path = 'stickers'
stickers = [load_image_with_alpha(os.path.join(stickers_path, f)) for f in os.listdir(stickers_path) if f.endswith('.png')]

class FiltersApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Editor")

        # Configure all columns to have the same width
        #for col in range(5):
        #   self.root.columnconfigure(col, weight=1)

        # Label to display image
        self.image_label = tk.Label(root)
        self.image_label.grid(row=0, column=0, columnspan=5, sticky="nsew")

        # Buttons for loading, capturing, and saving image
        self.load_image_button = tk.Button(root, text="Load Image", command=self.load_image)
        self.load_image_button.grid(row=1, column=0, sticky="ew")

        self.capture_image_button = tk.Button(root, text="Capture Image", command=self.capture_image)
        self.capture_image_button.grid(row=1, column=1, sticky="ew")

        self.save_image_button = tk.Button(root, text="Save Image", command=self.save_image)
        self.save_image_button.grid(row=1, column=2, sticky="ew")
        self.save_image_button.config(state="disabled")  # Disable until an image is loaded

        # Dropdown menu for selecting filters
        self.filter_var = tk.StringVar(root)
        self.filters = ['gray', 'blur', 'canny', 'invert', 'sepia', 'emboss', 'sharpen', 'threshold', 'sobel_x', 'edges']
        self.filter_menu = ttk.Combobox(root, textvariable=self.filter_var, values=self.filters)
        self.filter_menu.grid(row=1, column=3, columnspan=2, sticky="ew")
        self.filter_menu.bind('<<ComboboxSelected>>', self.apply_filter)

        # Buttons for selecting stickers
        self.sticker_buttons = []
        for i, sticker in enumerate(stickers):
            if sticker is not None:
                btn = tk.Button(root, text=f"Sticker {i+1}", command=lambda i=i: self.select_sticker(i), width=15)
                btn.grid(row=2 + i // 5, column=i % 5, sticky="ew")
                self.sticker_buttons.append(btn)

        # Initialize variables
        self.current_sticker = None
        self.original_image = None
        self.display_image = None
        self.cap = None
        self.video_running = False
        self.sticker_history = []  # List to keep track of sticker placements

    # Method to load an image from file
    def load_image(self):
        # Stop video stream if running
        if self.video_running:
            self.video_running = False
            self.cap.release()
            self.cap = None

        file_path = filedialog.askopenfilename()
        if file_path:
            self.original_image = cv.imread(file_path)
            self.display_image = self.original_image.copy()
            self.show_image()
            self.save_image_button.config(state="normal")

    # Method to start/stop video stream from webcam
    def start_video_stream(self):
        if not self.cap:
            self.cap = cv.VideoCapture(0)
        self.video_running = True
        self.update_video_stream()

    def update_video_stream(self):
        if self.video_running:
            ret, frame = self.cap.read()
            if ret:
                self.original_image = frame
                self.display_image = self.original_image.copy()
                self.apply_filter(None)
            self.root.after(10, self.update_video_stream)

    # Method to start/stop video stream from webcam
    def capture_image(self):
        if self.video_running:
            self.video_running = False  # Stop video stream
            self.cap.release()  # Release webcam
            self.cap = None
            self.save_image_button.config(state="normal")
        else:
            self.start_video_stream()  # Reopen webcam

    # Method to save the current displayed image
    def save_image(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".jpg")
        if file_path and self.display_image is not None:
            cv.imwrite(file_path, self.display_image)
            print(f"Image saved as {file_path}")

    # Method to apply selected filter to the image
    def apply_filter(self, event):
        if self.original_image is not None:
            filter_type = self.filter_var.get()
            self.display_image = self.original_image.copy()
            filtered_image = apply_filter(self.display_image, filter_type)
            self.display_image = filtered_image if filtered_image.ndim == 3 else cv.cvtColor(filtered_image, cv.COLOR_GRAY2BGR)
            self.show_image()

    # Method to select a sticker from the sticker list
    def select_sticker(self, index):
        self.current_sticker = stickers[index]
        print(f"Sticker {index + 1} selected.")
        self.image_label.bind("<Button-1>", self.place_sticker)

    # Method to place the selected sticker on the image
    def place_sticker(self, event):
        if self.current_sticker is not None and self.display_image is not None:
            x, y = event.x, event.y
            h, w = self.current_sticker.shape[:2]
            overlay = self.display_image.copy()

            # Calculate the top-left corner coordinates of the sticker to center it
            start_x = x - w // 2
            start_y = y - h // 2

            self.sticker_history.append((start_x, start_y, self.current_sticker.copy()))  # Add to history

            # Overlay the sticker on the image
            for i in range(h):
                for j in range(w):
                    if start_y + i < overlay.shape[0] and start_x + j < overlay.shape[1] and start_y + i >= 0 and start_x + j >= 0:
                        if self.current_sticker[i, j][3] > 0:  # If the pixel is not transparent
                            overlay[start_y + i, start_x + j] = self.current_sticker[i, j][:3]

            self.display_image = overlay
            self.show_image()

    # Method to rollback the last placed sticker
    def rollback_sticker(self):
        if self.sticker_history:
            start_x, start_y, sticker = self.sticker_history[-1]  # Get the last sticker from history
            overlay = self.display_image.copy()  # Start with the current display image

            h, w = sticker.shape[:2]
            for i in range(h):
                for j in range(w):
                    if start_y + i < overlay.shape[0] and start_x + j < overlay.shape[1] and start_y + i >= 0 and start_x + j >= 0:
                        if sticker[i, j][3] > 0:  # If the pixel is not transparent
                            overlay[start_y + i, start_x + j] = self.original_image[start_y + i, start_x + j]

            self.display_image = overlay
            self.show_image()

            # Remove the last sticker from history
            self.sticker_history.pop()

    # Method to display the image on the GUI
    def show_image(self):
        image_rgb = cv.cvtColor(self.display_image, cv.COLOR_BGR2RGB)
        image_pil = Image.fromarray(image_rgb)
        image_tk = ImageTk.PhotoImage(image_pil)
        self.image_label.config(image=image_tk)
        self.image_label.image = image_tk

    # Method to handle closing of the application
    def on_closing(self):
        if self.cap:
            self.cap.release()
        self.root.destroy()

# Main function to start the application
if __name__ == '__main__':
    root = tk.Tk()
    app = FiltersApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)

    # Create a button for rollback
    rollback_button = tk.Button(root, text="Rollback", command=app.rollback_sticker)
    rollback_button.grid(row=1, column=3, sticky="ew")

    app.start_video_stream() # Start the video stream
    root.mainloop() # Start the main GUI loop