import os
import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QListWidget, QLabel, 
                             QLineEdit, QFileDialog, QMessageBox, QTextEdit,
                             QSplitter, QFrame, QGroupBox)
from PyQt6.QtCore import Qt
import shutil
import json
import glob
from datetime import datetime
from io import StringIO

# A class to redirect stdout and stderr to a QTextEdit widget
class StreamRedirector(object):
    def __init__(self, text_edit):
        self.text_edit = text_edit
    
    def write(self, text):
        self.text_edit.insertPlainText(text)
        QApplication.processEvents() # Process events to ensure UI updates
    
    def flush(self):
        pass

class GameBackupGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Game Save Backup Utility")
        self.setGeometry(100, 100, 900, 650)
        
        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Left panel for game list and controls
        left_panel = QFrame()
        left_panel.setFrameShape(QFrame.Shape.StyledPanel)
        left_layout = QVBoxLayout(left_panel)
        
        # Game list
        self.game_list = QListWidget()
        self.game_list.itemSelectionChanged.connect(self.on_game_selected)
        left_layout.addWidget(QLabel("Configured Games:"))
        left_layout.addWidget(self.game_list)
        
        # Backup location group
        backup_loc_group = QGroupBox("Backup Location")
        backup_loc_layout = QVBoxLayout(backup_loc_group)
        
        self.backup_path_input = QLineEdit()
        self.backup_path_input.setReadOnly(True)
        backup_loc_layout.addWidget(self.backup_path_input)
        
        browse_backup_btn = QPushButton("Select Backup Directory")
        browse_backup_btn.clicked.connect(self.browse_backup_path)
        backup_loc_layout.addWidget(browse_backup_btn)
        
        left_layout.addWidget(backup_loc_group)

        # Add game section
        add_game_group = QGroupBox("Add New Game")
        add_game_layout = QVBoxLayout(add_game_group)
        
        self.game_name_input = QLineEdit()
        self.game_name_input.setPlaceholderText("Game Name")
        add_game_layout.addWidget(self.game_name_input)
        
        path_layout = QHBoxLayout()
        self.game_path_input = QLineEdit()
        self.game_path_input.setPlaceholderText("Save File Path")
        path_layout.addWidget(self.game_path_input)
        
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_path)
        path_layout.addWidget(browse_btn)
        
        add_game_layout.addLayout(path_layout)
        
        add_btn = QPushButton("Add Game")
        add_btn.clicked.connect(self.add_game)
        add_game_layout.addWidget(add_btn)
        
        left_layout.addWidget(add_game_group)
        
        # Action buttons group
        action_group = QGroupBox("Game Actions")
        action_layout = QVBoxLayout(action_group)
        
        remove_btn = QPushButton("Remove Selected Game")
        remove_btn.clicked.connect(self.remove_game)
        action_layout.addWidget(remove_btn)
        
        replace_btn = QPushButton("Replace Backup for Selected")
        replace_btn.clicked.connect(self.replace_backup)
        action_layout.addWidget(replace_btn)
        
        left_layout.addWidget(action_group)
        
        # Backup options group
        backup_group = QGroupBox("Backup Options")
        backup_layout = QVBoxLayout(backup_group)
        
        backup_replace_btn = QPushButton("Backup All Games (Replace Old)")
        backup_replace_btn.clicked.connect(self.backup_all_replace)
        backup_layout.addWidget(backup_replace_btn)
        
        backup_preserve_btn = QPushButton("Backup All Games (Keep Old)")
        backup_preserve_btn.clicked.connect(self.backup_all_preserve)
        backup_layout.addWidget(backup_preserve_btn)
        
        left_layout.addWidget(backup_group)
        
        # Right panel for log display
        right_panel = QFrame()
        right_panel.setFrameShape(QFrame.Shape.StyledPanel)
        right_layout = QVBoxLayout(right_panel)
        
        # Main log section
        log_group = QGroupBox("Activity Log")
        log_layout = QVBoxLayout(log_group)
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        log_layout.addWidget(self.log_display)
        right_layout.addWidget(log_group)
        
        # Interactive console section
        self.console_group = QGroupBox("Console (Press ` or ~ to toggle)")
        self.console_group.setVisible(False)  # Hidden by default
        console_layout = QVBoxLayout(self.console_group)
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        self.console_input = QLineEdit()
        self.console_input.returnPressed.connect(self.execute_command)
        
        console_layout.addWidget(self.console_output)
        console_layout.addWidget(self.console_input)
        right_layout.addWidget(self.console_group)

        # Add panels to main layout
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([350, 550])
        main_layout.addWidget(splitter)
        
        # Load initial data
        self.load_config()
        self.load_log()
    
    def keyPressEvent(self, event):
        """Overrides the key press event to toggle the console."""
        if event.key() == Qt.Key.Key_Apostrophe:
            self.console_group.setVisible(not self.console_group.isVisible())
            if self.console_group.isVisible():
                self.console_input.setFocus()
            event.accept()
        else:
            super().keyPressEvent(event)

    def execute_command(self):
        """Executes a Python command typed in the console."""
        command = self.console_input.text()
        self.console_input.clear()
        
        # Redirect stdout and stderr to the console output widget
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = StreamRedirector(self.console_output)
        sys.stderr = StreamRedirector(self.console_output)
        
        self.console_output.append(f">>> {command}")
        
        # This is a powerful feature, but can be a security risk.
        # Only use this on a trusted application and with trusted input.
        try:
            # We use exec() to allow multi-line statements and assignments
            exec(command, globals(), locals())
        except Exception as e:
            self.console_output.append(f"Error: {e}")
        finally:
            # Restore stdout and stderr
            sys.stdout = old_stdout
            sys.stderr = old_stderr

    def load_config(self):
        """Loads configuration from games.json, including backup path and games."""
        self.config = {}
        if os.path.exists('games.json'):
            with open('games.json', 'r') as f:
                try:
                    self.config = json.load(f)
                except json.JSONDecodeError:
                    self.log(f"Warning: games.json is empty or corrupted. Creating a new one.")
        
        self.games = self.config.get('games', {})
        self.backup_dir = self.config.get('backup_dir', 'GameBackups')
        
        self.backup_path_input.setText(self.backup_dir)
        self.refresh_game_list()
        
    def save_config(self):
        """Saves the current configuration to games.json."""
        self.config['games'] = self.games
        self.config['backup_dir'] = self.backup_dir
        with open('games.json', 'w') as f:
            json.dump(self.config, f, indent=4)
        self.log("Configuration saved.")

    def refresh_game_list(self):
        self.game_list.clear()
        for game_name in self.games.keys():
            self.game_list.addItem(game_name)
    
    def on_game_selected(self):
        selected_items = self.game_list.selectedItems()
        if selected_items:
            game_name = selected_items[0].text()
            if game_name in self.games:
                self.game_name_input.setText(game_name)
                self.game_path_input.setText(self.games[game_name])
    
    def browse_path(self):
        path = QFileDialog.getExistingDirectory(self, "Select Save Directory")
        if path:
            self.game_path_input.setText(path)
    
    def browse_backup_path(self):
        path = QFileDialog.getExistingDirectory(self, "Select Backup Directory")
        if path:
            self.backup_dir = path
            self.backup_path_input.setText(path)
            self.save_config()
            self.log(f"Backup directory set to: {self.backup_dir}")
    
    def add_game(self):
        game_name = self.game_name_input.text().strip()
        save_path = self.game_path_input.text().strip()
        
        if not game_name or not save_path:
            QMessageBox.warning(self, "Input Error", "Please provide both a game name and save path.")
            return
        
        if not os.path.exists(save_path):
            QMessageBox.warning(self, "Path Error", f"The path '{save_path}' does not exist.")
            return
        
        self.games[game_name] = save_path
        self.save_config()
        
        self.log(f"Added game: {game_name}")
        self.refresh_game_list()
        self.game_name_input.clear()
        self.game_path_input.clear()
    
    def remove_game(self):
        selected_items = self.game_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selection Error", "Please select a game to remove.")
            return
        
        game_name = selected_items[0].text()
        reply = QMessageBox.question(self, "Confirm Removal", 
                                     f"Are you sure you want to remove '{game_name}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            if game_name in self.games:
                del self.games[game_name]
                self.save_config()
                self.log(f"Removed game: {game_name}")
                self.refresh_game_list()
    
    def backup_all_replace(self):
        if not self.games:
            QMessageBox.information(self, "No Games", "No games are configured for backup.")
            return
        
        self.log("Starting backup of all games (replacing old backups)...")
        os.makedirs(self.backup_dir, exist_ok=True)
        
        backed_up = 0
        for game_name, source_path in self.games.items():
            if not os.path.exists(source_path):
                self.log(f"Warning: Source path for '{game_name}' does not exist. Skipping.")
                continue
                
            # Remove existing backups for this game
            existing_backups = glob.glob(os.path.join(self.backup_dir, f"{game_name}_backup_*"))
            for backup_folder in existing_backups:
                try:
                    if os.path.isdir(backup_folder):
                        shutil.rmtree(backup_folder)
                    else:
                        os.remove(backup_folder)
                    self.log(f"Deleted old backup: {backup_folder}")
                except OSError as e:
                    self.log(f"Error deleting old backup {backup_folder}: {e}")
            
            # Create new backup
            try:
                timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                dest_path = os.path.join(self.backup_dir, f"{game_name}_backup_{timestamp}")
                
                if os.path.isdir(source_path):
                    shutil.copytree(source_path, dest_path)
                else:
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    shutil.copy(source_path, dest_path)
                
                self.log(f"Backed up '{game_name}' to '{dest_path}'")
                backed_up += 1
            except Exception as e:
                self.log(f"Error backing up '{game_name}': {e}")
        
        self.log(f"Backup completed. {backed_up} games backed up (old backups replaced).")
        QMessageBox.information(self, "Backup Complete", f"Backup completed. {backed_up} games backed up (old backups replaced).")
    
    def backup_all_preserve(self):
        if not self.games:
            QMessageBox.information(self, "No Games", "No games are configured for backup.")
            return
        
        self.log("Starting backup of all games (preserving old backups)...")
        os.makedirs(self.backup_dir, exist_ok=True)
        
        backed_up = 0
        for game_name, source_path in self.games.items():
            if not os.path.exists(source_path):
                self.log(f"Warning: Source path for '{game_name}' does not exist. Skipping.")
                continue
                
            # Create new backup without removing old ones
            try:
                timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                dest_path = os.path.join(self.backup_dir, f"{game_name}_backup_{timestamp}")
                
                if os.path.isdir(source_path):
                    shutil.copytree(source_path, dest_path)
                else:
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    shutil.copy(source_path, dest_path)
                
                self.log(f"Backed up '{game_name}' to '{dest_path}'")
                backed_up += 1
            except Exception as e:
                self.log(f"Error backing up '{game_name}': {e}")
        
        self.log(f"Backup completed. {backed_up} games backed up (old backups preserved).")
        QMessageBox.information(self, "Backup Complete", f"Backup completed. {backed_up} games backed up (old backups preserved).")
    
    def replace_backup(self):
        selected_items = self.game_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selection Error", "Please select a game to replace backup for.")
            return
        
        game_name = selected_items[0].text()
        if game_name not in self.games:
            QMessageBox.warning(self, "Error", f"Game '{game_name}' not found in configuration.")
            return
        
        source_path = self.games[game_name]
        if not os.path.exists(source_path):
            QMessageBox.warning(self, "Error", f"Source path for '{game_name}' does not exist.")
            return
        
        # Remove existing backups
        existing_backups = glob.glob(os.path.join(self.backup_dir, f"{game_name}_backup_*"))
        if existing_backups:
            reply = QMessageBox.question(self, "Confirm Replacement", 
                                         f"This will delete {len(existing_backups)} existing backup(s) for '{game_name}'. Continue?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        for backup_folder in existing_backups:
            try:
                if os.path.isdir(backup_folder):
                    shutil.rmtree(backup_folder)
                else:
                    os.remove(backup_folder)
                self.log(f"Deleted old backup: {backup_folder}")
            except OSError as e:
                self.log(f"Error deleting old backup {backup_folder}: {e}")
        
        # Create new backup
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            dest_path = os.path.join(self.backup_dir, f"{game_name}_backup_{timestamp}")
            
            if os.path.isdir(source_path):
                shutil.copytree(source_path, dest_path)
            else:
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                shutil.copy(source_path, dest_path)
            
            self.log(f"Created new backup for '{game_name}' at '{dest_path}'")
            QMessageBox.information(self, "Success", f"Backup replaced for '{game_name}'.")
        except Exception as e:
            self.log(f"Error creating backup for '{game_name}': {e}")
            QMessageBox.critical(self, "Error", f"Failed to create backup: {e}")
    
    def log(self, message):
        """Logs a message to both the GUI and the log file."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.log_display.append(f"[{timestamp}] {message}")
        try:
            with open('backup_log.txt', 'a') as f:
                f.write(f"[{timestamp}] {message}\n")
        except Exception as e:
            self.log_display.append(f"Error writing to log file: {e}")
    
    def load_log(self):
        """Loads and displays the content of the log file."""
        if os.path.exists('backup_log.txt'):
            try:
                with open('backup_log.txt', 'r') as f:
                    content = f.read()
                    self.log_display.setPlainText(content)
            except Exception as e:
                self.log_display.append(f"Could not load existing log file: {e}")

def main():
    app = QApplication(sys.argv)
    window = GameBackupGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
