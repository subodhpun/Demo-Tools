// Constants
const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB
const allowedTypes = ['image/jpeg', 'image/png', 'image/gif'];

// Set default values and constraints
document.addEventListener('DOMContentLoaded', () => {
    const fontSize = document.getElementById('fontSize');
    const watermarkCount = document.getElementById('watermarkCount');
   
    // Set default values
    fontSize.value = '40';
    watermarkCount.value = '1';
   
    // Set constraints
    fontSize.min = '1';
    fontSize.max = '500';
    watermarkCount.min = '1';
    watermarkCount.max = '10';
});

// Form submission handler
document.getElementById('watermarkForm').addEventListener('submit', async (e) => {
    e.preventDefault();
   
    // Validate form
    const form = e.target;
    const formData = new FormData(form);
   
    // Show loading, hide error and result
    document.getElementById('loading').classList.remove('hidden');
    document.getElementById('error').classList.add('hidden');
    document.getElementById('result').classList.add('hidden');
   
    try {
        const response = await fetch('/watermark', {
            method: 'POST',
            body: formData
        });
       
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to generate watermark');
        }
       
        const blob = await response.blob();
        const imageUrl = URL.createObjectURL(blob);
       
        // Show result
        const watermarkedImage = document.getElementById('watermarkedImage');
        const downloadBtn = document.getElementById('downloadBtn');
       
        watermarkedImage.src = imageUrl;
        downloadBtn.href = imageUrl;
       
        // Set download filename based on original filename
        const originalFile = formData.get('file');
        const downloadFilename = `watermarked_${originalFile.name}`;
        downloadBtn.download = downloadFilename;
       
        document.getElementById('result').classList.remove('hidden');
    } catch (error) {
        document.getElementById('error').textContent = error.message;
        document.getElementById('error').classList.remove('hidden');
    } finally {
        document.getElementById('loading').classList.add('hidden');
    }
});

// File input handler
document.querySelector('input[type="file"]').addEventListener('change', (e) => {
    const file = e.target.files[0];
    const errorElement = document.getElementById('error');
   
    if (file) {
        // Validate file type
        if (!allowedTypes.includes(file.type)) {
            errorElement.textContent = 'Invalid file type. Allowed types: JPG, PNG, GIF';
            errorElement.classList.remove('hidden');
            e.target.value = '';
            return;
        }
       
        // Validate file size
        if (file.size > MAX_FILE_SIZE) {
            errorElement.textContent = 'File size exceeds 5MB limit';
            errorElement.classList.remove('hidden');
            e.target.value = '';
            return;
        }
       
        // Clear any previous errors
        errorElement.classList.add('hidden');
       
        // Show preview
        const reader = new FileReader();
        reader.onload = function(e) {
            const previewImage = document.getElementById('previewImage');
            previewImage.src = e.target.result;
            document.getElementById('preview').classList.remove('hidden');
        }
        reader.readAsDataURL(file);
    }
});

// Cleanup function for URL.createObjectURL
window.addEventListener('beforeunload', () => {
    const watermarkedImage = document.getElementById('watermarkedImage');
    if (watermarkedImage.src) {
        URL.revokeObjectURL(watermarkedImage.src);
    }
});
