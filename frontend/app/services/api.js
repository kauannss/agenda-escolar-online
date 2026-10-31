import axios from 'axios'

const api = axios.create({
    baseURL: '/api/auth',
    withCredentials: true,
})

export default api