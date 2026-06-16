/**
 * auth.js — Faculty login with JWT token management.
 */

import { saveToken, clearToken } from "@/lib/api"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"

/**
 * Calls POST /api/auth/login
 * On success, saves the JWT token to localStorage.
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

    // Save JWT token for subsequent authenticated requests
    if (data.token) {
      saveToken(data.token)
    }

    // Save user info
    if (typeof window !== "undefined") {
      localStorage.setItem(
        "ra_user",
        JSON.stringify({ email, displayName: data.name || email.split("@")[0] })
      )
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
        "Unable to reach the server. Is the backend running?",
    }
  }
}

export async function logout() {
  clearToken()
  return { success: true }
}

export function getCurrentUser() {
  if (typeof window === "undefined") return null
  const raw = localStorage.getItem("ra_user")
  if (!raw) return null
  try { return JSON.parse(raw) } catch { return null }
}

// Firebase-compatible interface (for easy migration)
export const auth = {
  signInWithEmailAndPassword: login,
  signOut: logout,
  currentUser: getCurrentUser,
}
