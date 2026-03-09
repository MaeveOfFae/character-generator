// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use serde::Deserialize;
use tauri_plugin_dialog::DialogExt;

#[derive(Deserialize)]
struct SaveDialogFilter {
    name: String,
    extensions: Vec<String>,
}

#[tauri::command]
async fn save_export(
    app: tauri::AppHandle,
    default_filename: String,
    filters: Option<Vec<SaveDialogFilter>>,
    data: Vec<u8>,
) -> Result<bool, String> {
    let mut dialog = app.dialog().file().set_file_name(default_filename);

    if let Some(filters) = filters {
        for filter in filters {
            let extensions: Vec<&str> = filter.extensions.iter().map(String::as_str).collect();
            dialog = dialog.add_filter(filter.name, &extensions);
        }
    }

    let Some(file_path) = dialog.blocking_save_file() else {
        return Ok(false);
    };

    let path = file_path.into_path().map_err(|error| error.to_string())?;
    std::fs::write(path, data).map_err(|error| error.to_string())?;

    Ok(true)
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![save_export])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
