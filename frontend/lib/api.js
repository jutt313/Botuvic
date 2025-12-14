const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

class APIClient {
  constructor() {
    this.baseURL = API_URL
    this.token = null
    this.loadToken()
  }

  loadToken() {
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('auth_token')
    }
  }

  setToken(token) {
    this.token = token
    if (typeof window !== 'undefined') {
      localStorage.setItem('auth_token', token)
    }
  }

  clearToken() {
    this.token = null
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token')
    }
  }

  async request(endpoint, options = {}) {
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    }

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`
    }

    const response = await fetch(`${this.baseURL}${endpoint}`, {
      ...options,
      headers,
    })

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`)
    }

    return response.json()
  }

  // Auth
  async login(email, password) {
    return this.request('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
  }

  async register(email, password, name) {
    return this.request('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, name }),
    })
  }

  async getCurrentUser() {
    return this.request('/api/auth/me')
  }

  // Projects
  async getProjects() {
    return this.request('/api/projects/')
  }

  async getProject(id) {
    return this.request(`/api/projects/${id}`)
  }

  async createProject(data) {
    return this.request('/api/projects/', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  // Metrics
  async getMetrics() {
    return this.request('/api/metrics')
  }

  async getActivityData(timeRange) {
    return this.request(`/api/metrics/activity?range=${timeRange}`)
  }
}

export const api = new APIClient()

