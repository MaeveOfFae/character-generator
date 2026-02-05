"""CustomTkinter GUI mockup for review screen."""

try:
    import customtkinter as ctk
except ImportError:
    print("Installing customtkinter...")
    import subprocess
    subprocess.check_call(["pip", "install", "customtkinter"])
    import customtkinter as ctk

from pathlib import Path


class ReviewScreenMockup(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Window config
        self.title("Blueprint UI - Review: elara_vance")
        self.geometry("1200x800")
        
        # Set theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Sample data
        self.assets = {
            "system_prompt": "You are Elara Vance, a cyber-noir detective...\n\n[Sample content would go here]",
            "post_history": "Elara leaned back in her chair, neon signs bleeding...\n\n[Sample content]",
            "character_sheet": "Name: Elara Vance\nAge: 34\nGender: Female\n...",
            "intro_scene": "Rain hammered the streets...",
            "intro_page": "# Elara Vance\n\nCyber-noir detective...",
            "a1111": "[Control]\n...",
            "suno": "[Control]\n...",
        }
        
        self.setup_ui()
    
    def setup_ui(self):
        # Main container
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Top bar with metadata
        self.create_top_bar()
        
        # Main content area
        self.create_main_area()
        
        # Bottom button bar
        self.create_button_bar()
    
    def create_top_bar(self):
        """Top bar with metadata and quick actions."""
        top_frame = ctk.CTkFrame(self, corner_radius=0)
        top_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        
        # Title
        title = ctk.CTkLabel(
            top_frame, 
            text="📝 Review: elara_vance",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title.pack(side="left", padx=10, pady=10)
        
        # Metadata info
        metadata_text = "Seed: Cyber-noir detective | Genre: Sci-fi/Noir | Mode: NSFW"
        metadata = ctk.CTkLabel(
            top_frame,
            text=metadata_text,
            font=ctk.CTkFont(size=12),
            text_color="gray70"
        )
        metadata.pack(side="left", padx=20)
        
        # Quick actions
        fav_btn = ctk.CTkButton(
            top_frame, 
            text="⭐ Favorite",
            width=100,
            command=lambda: print("Toggle favorite")
        )
        fav_btn.pack(side="right", padx=5, pady=10)
        
        tags_btn = ctk.CTkButton(
            top_frame,
            text="🏷️ Tags",
            width=100,
            command=lambda: print("Edit tags")
        )
        tags_btn.pack(side="right", padx=5)
        
        genre_btn = ctk.CTkButton(
            top_frame,
            text="🎭 Genre",
            width=100,
            command=lambda: print("Edit genre")
        )
        genre_btn.pack(side="right", padx=5)
    
    def create_main_area(self):
        """Main tabbed area with text editors."""
        main_frame = ctk.CTkFrame(self)
        main_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        
        # Create tabview
        self.tabview = ctk.CTkTabview(main_frame)
        self.tabview.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Add tabs with text boxes
        tabs = [
            "System Prompt",
            "Post History", 
            "Character Sheet",
            "Intro Scene",
            "Intro Page",
            "A1111",
            "Suno"
        ]
        
        self.textboxes = {}
        asset_keys = list(self.assets.keys())
        
        for i, tab_name in enumerate(tabs):
            # Add tab
            self.tabview.add(tab_name)
            
            # Create scrollable textbox
            asset_key = asset_keys[i]
            textbox = ctk.CTkTextbox(
                self.tabview.tab(tab_name),
                wrap="word",
                font=ctk.CTkFont(family="Courier", size=12)
            )
            textbox.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Insert content
            textbox.insert("1.0", self.assets[asset_key])
            textbox.configure(state="disabled")  # Read-only initially
            
            self.textboxes[asset_key] = textbox
    
    def create_button_bar(self):
        """Bottom button bar with actions."""
        button_frame = ctk.CTkFrame(self, corner_radius=0)
        button_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(5, 10))
        
        # Left side buttons
        edit_btn = ctk.CTkButton(
            button_frame,
            text="✏️ Edit Mode",
            width=120,
            command=self.toggle_edit
        )
        edit_btn.pack(side="left", padx=5, pady=10)
        
        save_btn = ctk.CTkButton(
            button_frame,
            text="💾 Save",
            width=100,
            fg_color="green",
            hover_color="darkgreen",
            command=lambda: print("Save changes")
        )
        save_btn.pack(side="left", padx=5)
        
        regen_btn = ctk.CTkButton(
            button_frame,
            text="🔄 Regenerate",
            width=120,
            command=lambda: print("Regenerate asset")
        )
        regen_btn.pack(side="left", padx=5)
        
        # Center status
        self.status_label = ctk.CTkLabel(
            button_frame,
            text="✓ Ready",
            font=ctk.CTkFont(size=12),
            text_color="lightgreen"
        )
        self.status_label.pack(side="left", padx=30)
        
        # Right side buttons
        back_btn = ctk.CTkButton(
            button_frame,
            text="⬅️ Back",
            width=100,
            command=self.quit
        )
        back_btn.pack(side="right", padx=5)
        
        export_btn = ctk.CTkButton(
            button_frame,
            text="📦 Export",
            width=100,
            fg_color="purple",
            hover_color="darkviolet",
            command=lambda: print("Export pack")
        )
        export_btn.pack(side="right", padx=5)
        
        validate_btn = ctk.CTkButton(
            button_frame,
            text="✓ Validate",
            width=100,
            command=lambda: print("Validate pack")
        )
        validate_btn.pack(side="right", padx=5)
    
    def toggle_edit(self):
        """Toggle edit mode on current tab."""
        current_tab = self.tabview.get()
        print(f"Toggle edit for: {current_tab}")
        # In real version: enable/disable textbox state


if __name__ == "__main__":
    app = ReviewScreenMockup()
    app.mainloop()
