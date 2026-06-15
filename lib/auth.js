/**
 * auth.js — Real faculty login against the MySQL backend.
 * Replaces the previous mock implementation.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"

/**
 * Calls POST /api/auth/login
 * Returns { success, message, name? }
 */
export async function login(email, password) {
  // Quick client-side check before hitting the server
  if (!email.toLowerCase().includes("srm")) {
    return {
      success: false,
      message: "Only SRM faculty email IDs are allowed",
    }
  }

  if (!password || password.length < 6) {
    return {
      success: false,
      message: "Password must be at least 6 characters",
    }
  }

  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    })

    const data = await res.json()

    if (!res.ok) {
      return {
        success: false,
        message: data?.message || `Login failed (${res.status})`,
      }
    }

    return {
      success: true,
      message: data.message || "Login successful",
      user: {
        email,
        displayName: data.name || email.split("@")[0],
      },
    }
  } catch (err) {
    return {
      success: false,
      message:
        err.message ||
        "Unable to reach the server. Is the backend running on port 8000?",
    }
  }
}

export async function logout() {
  // Stateless — nothing to do on the server side
  return { success: true }
}

export function getCurrentUser() {
  return null
}

// Firebase-compatible interface (for easy migration)
export const auth = {
  signInWithEmailAndPassword: login,
  signOut: logout,
  currentUser: getCurrentUser,
}
