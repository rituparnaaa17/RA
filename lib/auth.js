// Mock authentication module
// This file can be easily replaced with Firebase Auth later

export async function login(email, password) {
  // Simulate network delay
  await delay(500)

  // Validation: Only allow SRM email addresses
  if (!email.toLowerCase().includes("srm")) {
    return {
      success: false,
      message: "Only SRM faculty email IDs are allowed",
    }
  }

  // Mock validation - in real implementation, verify against database
  if (!password || password.length < 6) {
    return {
      success: false,
      message: "Password must be at least 6 characters",
    }
  }

  // Successful login
  return {
    success: true,
    user: {
      email: email,
      displayName: extractNameFromEmail(email),
      uid: generateMockUID(email),
    },
  }
}

export async function logout() {
  await delay(300)
  return { success: true }
}

export function getCurrentUser() {
  // In real implementation, this would check session/token
  // For mock, we return null (user should login)
  return null
}

// Helper functions
function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function extractNameFromEmail(email) {
  const username = email.split("@")[0]
  return username
    .split(".")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ")
}

function generateMockUID(email) {
  // Simple hash-like ID generation for mock purposes
  let hash = 0
  for (let i = 0; i < email.length; i++) {
    hash = (hash << 5) - hash + email.charCodeAt(i)
    hash = hash & hash
  }
  return "user_" + Math.abs(hash).toString(36)
}

// Firebase-compatible interface (for easy migration)
export const auth = {
  signInWithEmailAndPassword: login,
  signOut: logout,
  currentUser: getCurrentUser,
}
