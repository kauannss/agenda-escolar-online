import axios from 'axios'

const api = axios.create({
    baseURL:
        process.env.NEXT_PUBLIC_API_URL ||
        (process.env.NODE_ENV === 'development'
            ? 'http://127.0.0.1:8080'
            : undefined),
    withCredentials: true,
            
})

export default api