// src/composables/useDeleteConfirm.js
import { useConfirm } from 'primevue/useconfirm'

/**
 * Composable per aprire sempre la stessa dialog di conferma "Danger Zone".
 *
 * @returns {Object} { confirmDelete }
 */
export function useDeleteConfirm() {
    const confirm = useConfirm()

    /**
     * Apri la dialog di conferma cancellazione.
     *
     * @param {Function} onAccept - funzione da eseguire se l’utente conferma
     * @param {Function} onReject - funzione da eseguire se l’utente annulla (default no-op)
     * @param {string} message  - testo dell’avviso (default “Do you want to delete this element?”)
     */
    function confirmDelete(onAccept, onReject = () => {}, message = 'Do you want to delete this element?') {
        confirm.require({
            group: 'firstConfirmDialog',
            message,
            header: 'Danger Zone',
            icon: 'pi pi-exclamation-triangle',
            acceptLabel: 'Delete',
            rejectLabel: 'Cancel',
            acceptProps: {
                label: 'Delete',
                severity: 'danger'
            },
            rejectProps: {
                label: 'Cancel',
                severity: 'secondary',
                outlined: true
            },
            accept: () => onAccept(),
            reject: () => onReject()
        })
    }

    return { confirmDelete }
}
