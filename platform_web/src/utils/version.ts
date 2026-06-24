// Version utility functions
import fs from 'fs'
import path from 'path'

// Function to read frontend version from VERSION file
export function getFrontendVersion(): string {
  try {
    const versionPath = path.resolve(__dirname, '../../VERSION')
    if (fs.existsSync(versionPath)) {
      const version = fs.readFileSync(versionPath, 'utf-8').trim()
      if (version) {
        return version
      }
    }
  } catch (error) {
    console.error('Failed to read frontend version:', error)
  }
  return '1.0.0'
}

// For browser environment, we'll need to use a different approach
// In Vite, we can use import.meta.env or a virtual module
export const FRONTEND_VERSION = '1.0.0'
