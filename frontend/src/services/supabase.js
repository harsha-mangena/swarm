/**
 * Supabase client and auth service
 */

import { createClient } from '@supabase/supabase-js'

// Get Supabase config from environment or use empty strings for local dev
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || ''
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || ''

// Create Supabase client (will be null if not configured)
export const supabase = supabaseUrl && supabaseAnonKey
    ? createClient(supabaseUrl, supabaseAnonKey)
    : null

/**
 * Check if Supabase is configured
 */
export const isSupabaseConfigured = () => {
    return Boolean(supabaseUrl && supabaseAnonKey)
}

/**
 * Sign up with email and password
 */
export const signUp = async (email, password) => {
    if (!supabase) throw new Error('Supabase not configured')

    const { data, error } = await supabase.auth.signUp({
        email,
        password,
    })

    if (error) throw error
    return data
}

/**
 * Sign in with email and password
 */
export const signIn = async (email, password) => {
    if (!supabase) throw new Error('Supabase not configured')

    const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
    })

    if (error) throw error
    return data
}

/**
 * Sign out
 */
export const signOut = async () => {
    if (!supabase) return

    const { error } = await supabase.auth.signOut()
    if (error) throw error
}

/**
 * Get current session
 */
export const getSession = async () => {
    if (!supabase) return null

    const { data, error } = await supabase.auth.getSession()
    if (error) throw error
    return data.session
}

/**
 * Get current user
 */
export const getUser = async () => {
    if (!supabase) return null

    const { data, error } = await supabase.auth.getUser()
    if (error) return null
    return data.user
}

/**
 * Subscribe to auth state changes
 */
export const onAuthStateChange = (callback) => {
    if (!supabase) return { data: { subscription: { unsubscribe: () => { } } } }

    return supabase.auth.onAuthStateChange((event, session) => {
        callback(event, session)
    })
}
