#!/usr/bin/env python3
"""
X360 Extractor GUI - Graphical interface for processing Xbox 360 games
Version: 1.0 - GUI with directory selection
Author: Automated script for complete Xbox 360 ROM management
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import platform
import subprocess
import zipfile
import shutil
import threading
import re
from pathlib import Path
import time

class X360CuratorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("X360 Extractor GUI v1.0")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Variables
        self.source_dir = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.processing = False
        
        # Set extract-xiso path (fixed location)
        self.extract_xiso_path = self.get_extract_xiso_path()
        
        # Setup interface
        self.setup_ui()
    
    def setup_ui(self):
        """Setup user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title area: show only the header logo centered (no text)
        title_label = None
        try:
            assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
            logo2_path = os.path.normpath(os.path.join(assets_dir, "logo2.png"))
            if os.path.isfile(logo2_path):
                # Use PhotoImage for PNG support in Tkinter and keep a reference
                self.logo_header_img = tk.PhotoImage(file=logo2_path)
                title_label = ttk.Label(main_frame, image=self.logo_header_img)
        except Exception:
            title_label = None

        # If logo wasn't loaded, create an empty spacer label to preserve layout
        if not title_label:
            title_label = ttk.Label(main_frame, text="", padding=(0,10))

        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Source directory
        ttk.Label(main_frame, text="Source directory (ZIPs/ISOs):").grid(
            row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.source_dir, width=50).grid(
            row=1, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=5)
        ttk.Button(main_frame, text="Browse", 
                  command=self.browse_source_dir).grid(
            row=1, column=2, pady=5)
        
        # Output directory
        ttk.Label(main_frame, text="Output directory:").grid(
            row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.output_dir, width=50).grid(
            row=2, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=5)
        ttk.Button(main_frame, text="Browse", 
                  command=self.browse_output_dir).grid(
            row=2, column=2, pady=5)
        
        # Action buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=3, pady=20)
        
        self.process_button = ttk.Button(button_frame, text="Process Games", 
                                        command=self.start_processing)
        self.process_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Clear Log", 
                  command=self.clear_log).pack(side=tk.LEFT, padx=5)
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # Log area
        ttk.Label(main_frame, text="Processing log:").grid(
            row=5, column=0, sticky=tk.W, pady=(10, 5))
        
        self.log_text = scrolledtext.ScrolledText(main_frame, height=20, width=80)
        self.log_text.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Configure expansion
        main_frame.rowconfigure(6, weight=1)
    
    def browse_source_dir(self):
        """Select source directory"""
        directory = filedialog.askdirectory(title="Select source directory")
        if directory:
            self.source_dir.set(directory)
    
    def browse_output_dir(self):
        """Select output directory"""
        directory = filedialog.askdirectory(title="Select output directory")
        if directory:
            self.output_dir.set(directory)
    
    def get_extract_xiso_path(self):
        """Get extract-xiso path with automatic OS detection"""
        import platform
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        system = platform.system().lower()
        
        # Select correct binary based on OS
        if system == "windows":
            extract_xiso_path = os.path.join(current_dir, "isoextract", "extract-xiso.exe")
        else:  # Linux, macOS, etc.
            extract_xiso_path = os.path.join(current_dir, "isoextract", "extract-xiso")
        
        # Check if the OS-specific binary exists
        if os.path.isfile(extract_xiso_path):
            # On Linux/macOS, ensure it's executable
            if system != "windows":
                try:
                    os.chmod(extract_xiso_path, 0o755)
                except:
                    pass  # Ignore permission errors
            
            # Verify it's executable (Windows doesn't need X_OK check)
            if system == "windows" or os.access(extract_xiso_path, os.X_OK):
                return extract_xiso_path
        
        # Fallback paths for Linux/macOS
        if system != "windows":
            fallback_paths = [
                os.path.join(current_dir, "extract-xiso"),
                "/usr/local/bin/extract-xiso",
                "/usr/bin/extract-xiso"
            ]
            
            for path in fallback_paths:
                if os.path.isfile(path) and os.access(path, os.X_OK):
                    return path
        
        return ""
    
    def log(self, message, color="black"):
        """Add message to log"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def clear_log(self):
        """Clear log area"""
        self.log_text.delete(1.0, tk.END)
    
    def start_processing(self):
        """Start processing in separate thread"""
        if self.processing:
            return
        
        # Validate fields
        if not self.source_dir.get():
            messagebox.showerror("Error", "Please select the source directory")
            return
        
        if not self.output_dir.get():
            messagebox.showerror("Error", "Please select the output directory")
            return
        
        if not self.extract_xiso_path:
            messagebox.showerror("Error", "extract-xiso not found in expected location")
            return
        
        # Verify extract-xiso exists and is executable
        if not os.path.isfile(self.extract_xiso_path):
            messagebox.showerror("Error", f"extract-xiso file not found at: {self.extract_xiso_path}")
            return
        
        # Check executable permissions (skip on Windows)
        system = platform.system().lower()
        if system != "windows" and not os.access(self.extract_xiso_path, os.X_OK):
            messagebox.showerror("Error", "extract-xiso is not executable")
            return
        
        # Start processing
        self.processing = True
        self.process_button.config(state='disabled')
        self.progress.start()
        
        # Execute in separate thread
        thread = threading.Thread(target=self.process_games)
        thread.daemon = True
        thread.start()
    
    def process_games(self):
        """Process games (executed in separate thread)"""
        try:
            self.log("=== STARTING PROCESSING ===")
            system_name = platform.system()
            self.log(f"Operating System: {system_name}")
            self.log(f"extract-xiso path: {self.extract_xiso_path}")
            
            source_dir = self.source_dir.get()
            output_dir = self.output_dir.get()
            
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            steps_completed = 0
            
            # STEP 1: Extract ZIPs
            if self.extract_zips(source_dir):
                steps_completed += 1
            
            # STEP 2: Process ISOs
            if self.process_isos(source_dir, output_dir):
                steps_completed += 1
            
            # Show summary
            self.show_summary(output_dir, steps_completed)
            
        except Exception as e:
            self.log(f"ERROR: {str(e)}")
            messagebox.showerror("Error", f"Error during processing: {str(e)}")
        finally:
            self.processing = False
            self.process_button.config(state='normal')
            self.progress.stop()
    
    def extract_zips(self, source_dir):
        """Extract ZIP files"""
        zip_files = [f for f in os.listdir(source_dir) 
                    if f.lower().endswith('.zip')]
        
        if not zip_files:
            self.log("No ZIP files found")
            return False
        
        self.log(f"Extracting {len(zip_files)} ZIP file(s)...")
        
        extracted = 0
        for zip_file in zip_files:
            zip_path = os.path.join(source_dir, zip_file)
            self.log(f"Extracting: {zip_file}")
            
            try:
                # Verify integrity
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.testzip()
                
                # Extract
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(source_dir)
                
                self.log(f"✓ Extracted: {zip_file}")
                extracted += 1
                
                # Remove ZIP after successful extraction
                os.remove(zip_path)
                self.log(f"✓ Removed ZIP: {zip_file}")
                
            except Exception as e:
                self.log(f"✗ Error extracting {zip_file}: {str(e)}")
        
        self.log(f"ZIPs extracted: {extracted} of {len(zip_files)}")
        return extracted > 0
    
    def clean_game_name(self, original_name):
        """Clean game name by removing region patterns"""
        clean_name = original_name
        
        # Remove common region and language patterns
        patterns = [
            r'\s*\([^)]*\)\s*$',  # Patterns like (Europe), (USA), etc.
        ]
        
        for pattern in patterns:
            clean_name = re.sub(pattern, '', clean_name)
            clean_name = re.sub(pattern, '', clean_name)  # Apply twice in case of multiple patterns
        
        # Remove extra spaces
        clean_name = clean_name.strip()
        
        # If empty, use original name
        if not clean_name:
            clean_name = original_name
        
        return clean_name
    
    def process_isos(self, source_dir, output_dir):
        """Process ISO files"""
        iso_files = [f for f in os.listdir(source_dir) 
                    if f.lower().endswith('.iso')]
        
        if not iso_files:
            self.log("No ISO files found")
            return False
        
        self.log(f"Processing {len(iso_files)} ISO file(s)...")
        
        processed = 0
        successful = 0
        
        for iso_file in iso_files:
            processed += 1
            iso_path = os.path.join(source_dir, iso_file)
            
            self.log(f"[{processed}/{len(iso_files)}] {iso_file}")
            
            if self.process_single_iso(iso_path, output_dir):
                successful += 1
                self.log(f"[{processed}/{len(iso_files)}] ✓ Processed successfully")
                
                # Remove ISO after successful processing
                try:
                    os.remove(iso_path)
                    self.log(f"[{processed}/{len(iso_files)}] ✓ ISO removed")
                except Exception as e:
                    self.log(f"[{processed}/{len(iso_files)}] ⚠ Could not remove ISO: {str(e)}")
            else:
                self.log(f"[{processed}/{len(iso_files)}] ✗ Processing error")
            
            self.log("----------------------------------------")
        
        self.log(f"ISOs processed: {successful} of {len(iso_files)}")
        return successful > 0
    
    def process_single_iso(self, iso_path, output_dir):
        """Process a single ISO"""
        try:
            iso_file = os.path.basename(iso_path)
            original_name = os.path.splitext(iso_file)[0]
            base_name = self.clean_game_name(original_name)
            
            self.log(f"  - Original name: {original_name}")
            self.log(f"  - Clean name: {base_name}")
            
            # Verify file exists and is not empty
            if not os.path.isfile(iso_path):
                self.log(f"  - ✗ ISO file does not exist: {iso_path}")
                return False
            
            iso_size = os.path.getsize(iso_path)
            if iso_size < 1000000:  # Less than 1MB
                self.log(f"  - ✗ ISO file appears to be empty or corrupted")
                return False
            
            # Create game directory
            game_dir = os.path.join(output_dir, base_name)
            
            # If already exists and has content, skip it
            if os.path.exists(game_dir):
                content_count = len([f for f in Path(game_dir).rglob('*') if f.is_file()])
                if content_count > 0:
                    self.log(f"  - Game already processed, skipping")
                    return True
                else:
                    self.log(f"  - Directory exists but empty, re-processing")
                    shutil.rmtree(game_dir)
            
            # Create destination directory
            os.makedirs(game_dir, exist_ok=True)
            
            # Extract ISO using extract-xiso
            self.log(f"  - Extracting ISO with extract-xiso...")
            
            # Get absolute paths
            iso_fullpath = os.path.abspath(iso_path)
            game_fullpath = os.path.abspath(game_dir)
            
            cmd = [self.extract_xiso_path, '-x', iso_fullpath, '-d', game_fullpath]
            
            self.log(f"    - Command: {' '.join(cmd)}")
            
            # Execute extract-xiso
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.log(f"  - ✓ ISO extracted successfully with extract-xiso")
                
                # Verify successful extraction
                if os.path.exists(game_dir):
                    content_count = len([f for f in Path(game_dir).rglob('*') if f.is_file()])
                    
                    if content_count > 0:
                        # Calculate directory size
                        total_size = sum(f.stat().st_size for f in Path(game_dir).rglob('*') if f.is_file())
                        size_mb = total_size / (1024 * 1024)
                        
                        if size_mb < 1024:
                            size_str = f"{size_mb:.1f}M"
                        else:
                            size_str = f"{size_mb/1024:.1f}G"
                        
                        self.log(f"  - Extraction completed: {content_count} files, Size: {size_str}")
                        
                        # Show some extracted files
                        files = [f.name for f in Path(game_dir).rglob('*') if f.is_file()][:10]
                        self.log(f"  - Extracted files (first 10):")
                        for file in files:
                            self.log(f"    - {file}")
                        
                        return True
                    else:
                        self.log(f"  - ✗ Extracted directory is empty")
                        shutil.rmtree(game_dir)
                        return False
                else:
                    self.log(f"  - ✗ Destination directory was not created")
                    return False
            else:
                self.log(f"  - ✗ Error executing extract-xiso: {result.stderr}")
                if os.path.exists(game_dir):
                    shutil.rmtree(game_dir)
                return False
                
        except Exception as e:
            self.log(f"  - ✗ Error processing ISO: {str(e)}")
            return False
    
    def show_summary(self, output_dir, steps_completed):
        """Show final summary"""
        self.log("=== FINAL SUMMARY ===")
        
        # Count processed games
        if os.path.exists(output_dir):
            game_dirs = [d for d in os.listdir(output_dir) 
                        if os.path.isdir(os.path.join(output_dir, d))]
            total_games = len(game_dirs)
        else:
            total_games = 0
            game_dirs = []
        
        self.log("==========================================")
        self.log(f"✓ GAMES PROCESSED: {total_games}")
        self.log("==========================================")
        self.log(f"📁 LOCATION: {output_dir}")
        self.log("🎮 GAMES READY TO USE")
        self.log("==========================================")
        
        # Show game list if there are few
        if total_games <= 10 and total_games > 0:
            self.log("PROCESSED GAMES:")
            for game_name in sorted(game_dirs):
                self.log(f"  ✓ {game_name}")
            self.log("==========================================")
        
        if steps_completed == 0:
            self.log("⚠ No files found to process")
        else:
            self.log("PROCESS COMPLETED SUCCESSFULLY!")
            self.log(f"✓ {steps_completed} step(s) executed")
        
        # Show completion message
        messagebox.showinfo("Process Completed", 
                           f"Processing finished.\n"
                           f"Games processed: {total_games}\n"
                           f"Steps executed: {steps_completed}")

def main():
    root = tk.Tk()
    app = X360CuratorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()