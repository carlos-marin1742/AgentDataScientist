import axios from "axios";

const API_URL = "http://localhost:8000"; // Adjust if your backend is hosted elsewhere

export const uploadCSV = async (file) => {
  const formData = new FormData();
  formData.append("file", file);
  const response = await axios.post(`${API_URL}/upload`, formData, {
    headers: {
      "Content-Type": "multipart/form-data"
    }
  });
  return response.data;
};