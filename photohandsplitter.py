import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw
import numpy as np
import zipfile
import os

class PhotoSplitterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Photo Splitter")

        self.img = None
        self.img_tk = None
        self.drawn_points = []
        self.all_polygons = []

        # Frames
        self.frame_top = tk.Frame(root)
        self.frame_top.pack(side=tk.TOP)

        self.frame_bottom = tk.Frame(root)
        self.frame_bottom.pack(side=tk.BOTTOM)

        # Buttons
        self.upload_button = tk.Button(self.frame_top, text="Upload Photo", command=self.upload_photo)
        self.upload_button.pack(side=tk.LEFT)

        self.paste_button = tk.Button(self.frame_top, text="Paste Photo", command=self.paste_photo)
        self.paste_button.pack(side=tk.LEFT)

        self.process_button = tk.Button(self.frame_top, text="Process", command=self.process_image)
        self.process_button.pack(side=tk.RIGHT)

        self.clear_button = tk.Button(self.frame_top, text="Clear", command=self.clear_drawings)
        self.clear_button.pack(side=tk.RIGHT)

        self.new_photo_button = tk.Button(self.frame_top, text="New Photo", command=self.new_photo)
        self.new_photo_button.pack(side=tk.RIGHT)

        # Canvas for images
        self.canvas_original = tk.Canvas(self.frame_bottom, width=500, height=500)
        self.canvas_original.pack(side=tk.LEFT)

        self.canvas_preview = tk.Canvas(self.frame_bottom, width=500, height=500)
        self.canvas_preview.pack(side=tk.RIGHT)

        # Bind mouse events to draw free-form shape
        self.canvas_preview.bind("<Button-1>", self.start_draw)
        self.canvas_preview.bind("<B1-Motion>", self.draw)
        self.canvas_preview.bind("<ButtonRelease-1>", self.end_draw)

    def upload_photo(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp;*.tiff")])
        if file_path:
            self.load_image(file_path)

    def paste_photo(self):
        try:
            from PIL import ImageGrab
            self.img = ImageGrab.grabclipboard()
            self.show_preview()
        except Exception as e:
            messagebox.showerror("Error", "Failed to paste image from clipboard")

    def load_image(self, file_path):
        try:
            self.img = Image.open(file_path)
            self.show_preview()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image: {e}")

    def show_preview(self):
        self.img_tk = ImageTk.PhotoImage(self.img.resize((500, 500)))
        self.canvas_original.create_image(0, 0, anchor=tk.NW, image=self.img_tk)
        self.canvas_preview.create_image(0, 0, anchor=tk.NW, image=self.img_tk)

    def start_draw(self, event):
        self.drawn_points = [(event.x, event.y)]

    def draw(self, event):
        self.drawn_points.append((event.x, event.y))
        if len(self.drawn_points) > 1:
            self.canvas_preview.create_line(self.drawn_points[-2], self.drawn_points[-1], fill="green", width=2)

    def end_draw(self, event):
        self.drawn_points.append((event.x, event.y))
        self.canvas_preview.create_line(self.drawn_points[-2], self.drawn_points[-1], fill="green", width=2)
        self.all_polygons.append(self.drawn_points)
        self.drawn_points = []

    def clear_drawings(self):
        self.canvas_preview.delete("all")
        self.show_preview()
        self.all_polygons = []

    def new_photo(self):
        self.clear_drawings()
        self.img = None
        self.canvas_original.delete("all")
        self.canvas_preview.delete("all")

    def process_image(self):
        try:
            if not self.img:
                raise ValueError("No image loaded")

            if not self.all_polygons:
                raise ValueError("No cut points defined")

            output_dir = filedialog.askdirectory()
            if not output_dir:
                raise ValueError("No output directory selected")

            zip_path = os.path.join(output_dir, "split_images.zip")
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for i, points in enumerate(self.all_polygons):
                    mask = Image.new('L', self.img.size, 0)
                    draw = ImageDraw.Draw(mask)
                    scaled_points = [(x * self.img.width // 500, y * self.img.height // 500) for x, y in points]
                    draw.polygon(scaled_points, outline=1, fill=255)

                    # Debugging output
                    print(f"Processing polygon {i+1} with points: {scaled_points}")

                    img_cut = Image.new("RGBA", self.img.size)
                    img_cut.paste(self.img, mask=mask)

                    piece_path = os.path.join(output_dir, f"cut_image_{i + 1}.png")
                    img_cut.save(piece_path)
                    zipf.write(piece_path, f"cut_image_{i + 1}.png")
                    os.remove(piece_path)

            messagebox.showinfo("Success", f"Images processed and saved to {zip_path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = PhotoSplitterApp(root)
    root.mainloop()
