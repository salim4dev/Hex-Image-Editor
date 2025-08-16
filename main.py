import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import binascii
import io

HEADER_SIZE = 200  # Premier 200 octets = entête à surligner

class ImageHexEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Hex Image Editor ")
        self.root.configure(bg='black')

        # Image display
        self.image_label = tk.Label(root, bg='black')
        self.image_label.grid(row=0, column=0, padx=5, pady=5)

        # Canvas + Scrollable hex grid
        self.canvas = tk.Canvas(root, bg='black', highlightthickness=0)
        self.scroll_y = tk.Scrollbar(root, orient='vertical', command=self.canvas.yview)
        self.scroll_x = tk.Scrollbar(root, orient='horizontal', command=self.canvas.xview)

        self.canvas.grid(row=0, column=1, padx=5, pady=5, sticky='nsew')
        self.scroll_y.grid(row=0, column=2, sticky='ns')
        self.scroll_x.grid(row=1, column=1, sticky='ew')

        self.hex_frame = tk.Frame(self.canvas, bg='black')
        self.canvas.create_window((0, 0), window=self.hex_frame, anchor='nw')
        self.canvas.config(yscrollcommand=self.scroll_y.set, xscrollcommand=self.scroll_x.set)

        self.hex_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        # Buttons
        btn_frame = tk.Frame(root, bg='black')
        btn_frame.grid(row=2, column=0, columnspan=2, pady=5)

        self._add_button(btn_frame, "Charger image", self.load_image)
        self._add_button(btn_frame, "Appliquer modifications", self.apply_changes)
        self._add_button(btn_frame, "Enregistrer", self.save_image)

        self.original_data = None
        self.image_path = None
        self.hex_entries = []  # List of Entry widgets

    def _add_button(self, parent, text, command):
        btn = tk.Button(parent, text=text, command=command, bg='#222', fg='lime',
                        activebackground='#444', activeforeground='white')
        btn.pack(side=tk.LEFT, padx=5)

    def load_image(self):
        filetypes = [("Image files", "*.png *.jpg *.jpeg *.bmp")]
        path = filedialog.askopenfilename(title="Choisir une image", filetypes=filetypes)
        if not path:
            return
        self.image_path = path

        with open(path, "rb") as f:
            self.original_data = f.read()

        self.show_image(self.original_data)
        self.build_hex_grid(self.original_data)

    def show_image(self, data):
        try:
            # Essayer d'afficher normalement
            img = Image.open(io.BytesIO(data))
            img.thumbnail((400, 400))
            self.tk_image = ImageTk.PhotoImage(img)
            self.image_label.config(image=self.tk_image)
        except Exception as e:
            # Image corrompue → fabrique un bruit visuel à la place
            fallback_img = self.create_noise_image(data)
            fallback_img.thumbnail((400, 400))
            self.tk_image = ImageTk.PhotoImage(fallback_img)
            self.image_label.config(image=self.tk_image)

    def create_noise_image(self, data):
        """ Crée une image bruitée (glitch style) à partir des données corrompues """
        import numpy as np

        size = int(len(data) ** 0.5)  # Taille approx carré
        size = max(32, min(size, 512))  # Clamp pour pas être minuscule

        # Remplit une matrice avec les données (R,G,B random)
        arr = np.frombuffer(data, dtype=np.uint8)
        arr = np.resize(arr, (size, size, 3))  # RGB

        img = Image.fromarray(arr, 'RGB')
        return img

    def validate_hex(self, P):
        """ Validation pour chaque Entry : max 2 caractères hex """
        if len(P) > 2:
            return False
        for c in P:
            if c not in '0123456789abcdefABCDEF':
                return False
        return True

    def build_hex_grid(self, data):
        # Clear old grid
        for widget in self.hex_frame.winfo_children():
            widget.destroy()
        self.hex_entries.clear()

        vcmd = (self.root.register(self.validate_hex), '%P')

        hex_data = binascii.hexlify(data).decode('utf-8')
        bytes_list = [hex_data[i:i+2] for i in range(0, len(hex_data), 2)]

        # Display as table (16 bytes/row)
        row = 0
        col = 0
        for idx, byte_str in enumerate(bytes_list):
            entry = tk.Entry(self.hex_frame, width=3, justify='center',
                             validate='key', validatecommand=vcmd)
            entry.insert(0, byte_str)

            # Couleurs style
            if idx < HEADER_SIZE:
                entry.config(bg='red', fg='white', insertbackground='white', font=('Consolas', 9, 'bold'))
            else:
                entry.config(bg='black', fg='lime', insertbackground='lime', font=('Consolas', 9))

            entry.grid(row=row, column=col, padx=1, pady=1)
            self.hex_entries.append(entry)

            col += 1
            if col >= 16:
                col = 0
                row += 1

        # Recalcule scroll
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def apply_changes(self):
        new_bytes = bytearray()
        for idx, entry in enumerate(self.hex_entries):
            val = entry.get().strip()
            if len(val) != 2:
                messagebox.showerror("Erreur HEX", f"Octet invalide à la position {idx}: '{val}' (exactement 2 chiffres hex)")
                return
            byte = int(val, 16)
            new_bytes.append(byte)

        self.original_data = bytes(new_bytes)
        self.show_image(self.original_data)

    def save_image(self):
        if not self.original_data:
            return
        save_path = filedialog.asksaveasfilename(defaultextension=".png",
                                                 filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp")])
        if save_path:
            with open(save_path, "wb") as f:
                f.write(self.original_data)
            messagebox.showinfo("Succès", f"Image enregistrée : {save_path}")

if __name__ == "__main__":
    root = tk.Tk()
    # Support du redimensionnement (grid expand)
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(1, weight=1)
    app = ImageHexEditor(root)
    root.mainloop()
