const STORAGE_KEY = 'son-of-anton:conversations'
const MAX_CONVERSATIONS = 50

// Callers pass the full in-memory list (which may include a conversation
// the user hasn't sent a message in yet) — strip those before writing so an
// unsaved-empty conversation never reaches localStorage, no matter which
// mutation (add/update/delete) triggered this write.
function saveConversations(conversations) {
  const persistable = conversations.filter((c) => (c.displayMessages?.length ?? 0) > 0)
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(persistable))
  } catch {
    // localStorage full — drop oldest (last entry, since list is newest-first) and retry
    if (persistable.length > 1) {
      const trimmed = persistable.slice(0, -1)
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(trimmed))
      } catch {
        // Give up silently — at least the in-memory state is correct
      }
    }
  }
}

export function loadConversations() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

export function createConversation(model) {
  return {
    id: crypto.randomUUID(),
    title: null,
    model,
    displayMessages: [],
    apiMessages: [],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  }
}

export function generateTitle(firstUserMessage) {
  return firstUserMessage.trim().slice(0, 40) || 'New conversation'
}

// Returns new conversations array (already persisted to localStorage)
export function addConversation(conversations, conversation) {
  const updated = [conversation, ...conversations].slice(0, MAX_CONVERSATIONS)
  saveConversations(updated)
  return updated
}

// Returns new conversations array (already persisted to localStorage)
export function updateConversation(conversations, id, updates) {
  const updated = conversations.map((c) =>
    c.id === id ? { ...c, ...updates, updatedAt: new Date().toISOString() } : c
  )
  saveConversations(updated)
  return updated
}

// Returns new conversations array (already persisted to localStorage)
export function deleteConversation(conversations, id) {
  const updated = conversations.filter((c) => c.id !== id)
  saveConversations(updated)
  return updated
}

// Drops any conversation with no messages and re-persists if anything
// changed. Used at load time to clean up empties saved before this existed.
export function pruneEmptyConversations(conversations) {
  const pruned = conversations.filter((c) => (c.displayMessages?.length ?? 0) > 0)
  if (pruned.length !== conversations.length) saveConversations(pruned)
  return pruned
}
