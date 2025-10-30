# GameSave Backup Tool

A lightweight and convenient tool to automatically back up your game save files. This ensures your progress is always safe, even if your game crashes, files get corrupted, or you switch devices.

---

## ✨ Features

* **Automatic Backups:** Backs up your game save files at regular intervals.
* **Custom Backup Paths:** Choose where your backups should be stored.
* **Multi-Game Support:** Works with multiple games by configuring paths.
* **Compression Support:** Optionally compress backups to save space.
* **Restore System:** Easily restore any previous save with one click.

---

## 📦 Installation

1. Clone the repository:

   ```bash
   git clone <your-repo-link>
   cd gamesave-backup-tool
   ```
2. Install requirements (if any):

   ```bash
   pip install -r requirements.txt
   ```
3. Run the tool:

   ```bash
   python main.py
   ```

---

## ⚙️ Configuration

Edit the `config.json` file to set:

* Game save directory paths
* Backup output directory
* Backup frequency
* Compression toggle

Example:

```json
{
  "games": [
    {
      "name": "Game Name",
      "save_path": "C:/Users/<username>/Documents/Game/Save"
    }
  ],
  "backup_directory": "./backups",
  "auto_backup_interval_minutes": 15,
  "compress_backups": true
}
```

---

## 🔄 Usage

* **Start Backup:** Run `main.py`.
* **Restore Save:** Use the `restore` option in the UI/CLI.
* **View Backup History:** Check the `backups` folder.

---

## 📝 License

This project is licensed under the MIT License.

---

## 🤝 Contributing

Pull requests are welcome! For ma
