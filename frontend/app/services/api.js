import axios from 'axios'

const api = axios.create({
    baseURL: '/api/backend',
    withCredentials: true,
})

export default api