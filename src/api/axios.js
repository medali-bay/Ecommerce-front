import axios from "axios";

const PUBLIC_ENDPOINTS = ["/products/", "/categories/", "/register/", "/token/"];

const api = axios.create({
  baseURL: "https://ecommerce-e9wm.onrender.com/api",
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("accessToken");
  const url = config.url || "";
  const isPublicGet =
    config.method === "get" &&
    PUBLIC_ENDPOINTS.some((endpoint) => url.startsWith(endpoint));

  if (token && !isPublicGet) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("accessToken");
      localStorage.removeItem("refreshToken");
      localStorage.removeItem("username");
      localStorage.removeItem("isAdmin");
    }

    return Promise.reject(error);
  }
);

export default api;
