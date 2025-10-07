export function getUniformTranslationStatuses(content) {
    if (content.translations.length === 0)
        return {status: "unprocessed", status_num: 0}

    let states = {
        "rifiutata": 0,
        "pending": 0,
        "validata": 0,
    }

    for (const t of content.translations) {
        if (t.status in states)
            states[t.status] += 1
    }
    if (states["rifiutata"] > 0) return {status: "rifiutata", status_num: states["rifiutata"]};
    if (states["pending"] > 0) return {status: "pending", status_num: states["pending"]};
    if (states["validata"] > 0) return {status: "validata", status_num: states["validata"]};
}


export function getUniformTranslationStates(content) {
    if (content.translations.length === 0)
        return {state: "unprocessed", state_num: 0}

    let states = {
        "sent": 0,
        "pending": 0,
        "success": 0,
        "failed": 0,
    }

    for (const t of content.translations) {
        if (t.state in states)
            states[t.state] += 1
    }
    if (states["sent"] > 0) return {state: "sent", state_num: states["sent"]};
    if (states["pending"] > 0) return {state: "pending", state_num: states["pending"]};
    if (states["success"] > 0) return {state: "success", state_num: states["success"]};
    if (states["failed"] > 0) return {state: "failed", state_num: states["failed"]};
}


export function getTranslationStatusClassColor(status) {
    switch (status) {
        case 'rifiutata':
            return 'text-bg-danger';
        case 'validata':
            return 'text-bg-success';
        case 'pending':
            return 'text-bg-primary';
        default:
            return 'text-bg-secondary';
    }
}


export function getTranslationStatusLabel(status) {
    switch (status) {
        case 'rifiutata':
            return 'rejected';
        case 'validata':
            return 'validated';
        case 'pending':
            return 'draft';
        default:
            return 'unprocessed';
    }
}