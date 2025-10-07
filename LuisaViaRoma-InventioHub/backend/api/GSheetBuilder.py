import google.auth
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from googleapiclient.errors import HttpError
import gspread

class GSheetBuilder:
    EMAILS = ['dev.team@inventiohub.com']
    credentials_file = "gsheet_creds.json"

    def __init__(self, credentials_file=None):
        cred_file = credentials_file or GSheetBuilder.credentials_file
        creds, project = google.auth.load_credentials_from_file(cred_file)
        # Se le credenziali sono scadute, chiedi l'autenticazione dell'utente
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
        ]

        # init Google Drive service
        self.drive_service = build('drive', 'v3', credentials=creds)
        service_creds = Credentials.from_service_account_file(cred_file, scopes=scopes)
        self.gc = gspread.authorize(service_creds)

    def list_files(self):
        results = self.drive_service.files().list(pageSize=10, fields="nextPageToken, files(id, name)").execute()
        files = results.get('files', [])
        if not files:
            print('drive has no files')
        else:
            print('Drive files:')
            for file in files:
                print(f"{file['name']} (ID: {file['id']})")
                file_id = file['id']

    def list_files_with_sizes(self):
        try:
            user_about = self.drive_service.about().get(fields="user, storageQuota").execute()
            print(user_about)
            # Get quota info
            about = self.drive_service.about().get(fields="storageQuota").execute()
            quota = about.get('storageQuota', {})
            usage = int(quota.get('usage', 0))
            limit = int(quota.get('limit', 0))
            print(f"Drive usage: {usage / (1024 ** 2):.2f} MB / {limit / (1024 ** 2):.2f} MB")

            # List files with size
            results = self.drive_service.files().list(
                pageSize=100,
                fields="nextPageToken, files(id, name, mimeType, size)"
            ).execute()

            files = results.get('files', [])
            if not files:
                print("Drive has no files.")
            else:
                print("Drive files:")
                for file in files:
                    name = file.get("name")
                    file_id = file.get("id")
                    mime_type = file.get("mimeType")
                    size = int(file.get("size", 0))  # Will be 0 or missing for folders
                    print(f"{name} (ID: {file_id}) - {mime_type} - Size: {size / 1024:.2f} KB")
        except HttpError as err:
            print(f"Error listing files or retrieving quota: {err}")


    def clear_files(self):
        results = self.drive_service.files().list(pageSize=10, fields="nextPageToken, files(id, name)").execute()
        files = results.get('files', [])
        for file in files:
            self.delete_file_or_folder(file['id'])

    def folder_exists(self, name, parent_folder_id=None):
        mime_type = 'application/vnd.google-apps.folder'
        query = f"name = '{name}' and mimeType = '{mime_type}' and trashed = false"
        if parent_folder_id:
            query += f" and '{parent_folder_id}' in parents"
        try:
            response = self.drive_service.files().list(q=query, fields="files(id, name)").execute()
        except HttpError as err:
            print(f"drive service error {err}")
            raise
        files = response.get('files', [])
        if files:
            return files[0]['id']
        return None

    def delete_file_or_folder(self, file_id):
        try:
            #file = self.drive_service.files().get(fileId=file_id, fields="id").execute()
            self.drive_service.files().delete(fileId=file_id).execute()
            print(f"File {file_id} eliminato con successo.")
        except HttpError as error:
            if error.resp.status == 404:
                print(f"Il file {file_id} non esiste.")
            else:
                print(f"Errore durante l'accesso o l'eliminazione del file: {error}")
            raise

    def make_folder(self, name, parent_folder_id=None, share=False):
        folder_metadata = {
            'name': name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        if parent_folder_id:
            folder_metadata['parents'] = [parent_folder_id]

        try:
            folder = self.drive_service.files().create(body=folder_metadata, fields='id').execute()
            folder_id = folder.get('id')
            if share:
                for mail in GSheetBuilder.EMAILS:
                    self._share_folder(folder_id, mail, 'reader')
                    #print(f"folder {folder_id} shared with {mail}")
        except HttpError as err:
            print(f"drive service error {err}")
            raise
        return folder_id

    def _share_folder(self, folder_id, email, role):
        permission = {
            'type': 'user',
            'role': role, # writer, reader
            'emailAddress': email 
        }
        self.drive_service.permissions().create(
            fileId=folder_id,
            body=permission,
            sendNotificationEmail=True
        ).execute()

    def create_sheet(self, folder_id, sheet_name):
        file_metadata = {
            'name': sheet_name,
            'mimeType': 'application/vnd.google-apps.spreadsheet',
            'parents': [folder_id]
        }
        try:
            file = self.drive_service.files().create(body=file_metadata, fields='id').execute()
            spreadsheet_id = file.get('id')
        except Exception:
            raise
        return spreadsheet_id

    def update_sheet(self, sheet_id):
        spreadsheet = self.gc.open_by_key(sheet_id)
        spreadsheet.sheet1.update_cell(1, 1, 'Hello world!')

    def append_row(self, sheet_id, data, header=None):
        # Example: data = ["Value 1", "Value 2", "Value 3"]
        sheet = self.gc.open_by_key(sheet_id).sheet1
        if header:
            sheet.insert_row(header, 1)  # insert at the first row
        if data:
            sheet.append_row(data)

    def append_row2(self, sheet_name, data, header=None):
        try:
            sheet = self.gc.open(sheet_name).sheet1
            if header:
                sheet.insert_row(header, 1)  # insert at the first row
            if data:
                sheet.append_row(data)
        except Exception as e:
            raise Exception(f"Unable to find spreadsheet '{sheet_name}': {str(e)}")

    def export_content(self, content):
        rows = []

        # Funzione helper per appiattire oggetti JSON annidati
        def flatten_json(data, parent_key='', sep='_'):
            """
            Appiattisce un dizionario JSON annidato in un dizionario piatto
            """
            items = []
            if isinstance(data, dict):
                for k, v in data.items():
                    new_key = f"{parent_key}{sep}{k}" if parent_key else k
                    if isinstance(v, dict):
                        items.extend(flatten_json(v, new_key, sep=sep).items())
                    elif isinstance(v, list):
                        # Per le liste, crea campi separati con indice
                        for i, item in enumerate(v):
                            if isinstance(item, dict):
                                items.extend(flatten_json(item, f"{new_key}[{i}]", sep=sep).items())
                            else:
                                items.append((f"{new_key}[{i}]", item))
                    else:
                        items.append((new_key, v))
            return dict(items)

        # Ottieni tutti i campi possibili dai dati del content e delle traduzioni
        all_fields = set()

        # Campi del content principale
        content_data_flat = flatten_json(content.data)
        all_fields.update(content_data_flat.keys())

        # Campi dalle traduzioni
        translations_data = []
        for trans in content.translations.all():
            trans_data_flat = flatten_json(trans.data)
            all_fields.update(trans_data_flat.keys())
            translations_data.append({
                'language': trans.language,
                'data': trans_data_flat,
                'status': trans.status,
                'rejection_message': trans.rejection_message
            })

        # Ordina i campi per consistenza
        field_names = sorted(list(all_fields))

        # Header row
        headers = [
                      'ID',
                      'Title',
                      'Created At',
                      'LLM Model',
                      'Language',
                  ] + field_names

        preheaders = ["#########" for _ in range(len(headers))]

        # Prima riga: content principale
        content_row = [
            content.id,
            content.title,
            content.created_at.strftime("%Y-%m-%d %H:%M:%S") if content.created_at else '',
            content.llmmodel.name if content.llmmodel else '',
            content.language.name,
        ]

        # Aggiungi i valori dei campi data
        for field in field_names:
            content_row.append(content_data_flat.get(field, ''))

        rows.append(content_row)

        # Righe successive: traduzioni
        for trans_info in translations_data:
            trans_row = [
                '',
                '',
                '',  # Created at (vuoto per traduzioni)
                '',  # LLM Model (vuoto per traduzioni)
                trans_info['language'].name,
            ]

            # Aggiungi i valori dei campi data della traduzione
            for field in field_names:
                trans_row.append(trans_info['data'].get(field, ''))

            rows.append(trans_row)

        # Ottieni o crea il foglio per questo tipo di contenuto
        sheet_name = content.content_type.name
        sheet = self.gc.open(sheet_name).sheet1

        # Prima scrivi gli headers
        sheet.append_row(preheaders)
        sheet.append_row(headers)

        # Poi scrivi tutte le righe
        for row in rows:
            sheet.append_row(row)

        return {
            'message': 'Content exported successfully',
            'rows_exported': len(rows),
            'sheet_name': sheet_name
        }


    def update_cell(self, sheet_name):
        sheet = self.gc.open(sheet_name).sheet1
        sheet.update_cell(1, 2, "Nuovo Valore")

    def share_file(self, sheet_name, email):
        sheet = self.gc.open(sheet_name)
        sheet.share(email, perm_type='user', role='reader')

    def create_file(self, name):
        spreadsheet = self.gc.create(name)

    def print_file(self, sheet_name):
        #sheet = self.gc.open_by_key(sheet_id)
        sheet = self.gc.open(sheet_name)
        values = sheet.sheet1.row_values(1)
        print(f"row values: {values}")

        s = sheet.sheet1
        value = s.cell(1, 1).value
        print(f"row 1 column 1: {value}")
        value = s.cell(1, 2).value 
        print(f"row 1 column 2: {value}")

def test():
    print("running GSheetBuilder...")
    cleanup = False
    gs = GSheetBuilder(credentials_file="../gsheet_creds.json")
    gs.list_files()
    #gs.append_row("123", ['prova1', 'prova2'])
    #gs.delete_file_or_folder("")
    '''
    try:
        folder_id = gs.make_folder("folder_test", share=True) 
        sheet_id = gs.create_sheet(folder_id, "sheet example 1")
        gs.append_row(sheet_id, ["test 1", "test 2"], ["col 1", "col 2"])
    except Exception as e:
        return print(str(e))
    '''

if __name__ == "__main__":
    test()
