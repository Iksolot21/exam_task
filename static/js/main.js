// Глобальные переменные для хранения данных
let imageData = {
    phantom: null,
    noisePhantom: null,
    r1: null,
    r2: null
};

// Функция для отображения индикатора загрузки
function showLoading(buttonId) {
    const button = document.getElementById(buttonId);
    button.disabled = true;
    
    // Добавить индикатор загрузки, если его еще нет
    if (!button.querySelector('.loading')) {
        const spinner = document.createElement('span');
        spinner.className = 'loading';
        button.appendChild(spinner);
    }
}

// Функция для скрытия индикатора загрузки
function hideLoading(buttonId) {
    const button = document.getElementById(buttonId);
    button.disabled = false;
    
    // Удалить индикатор загрузки
    const spinner = button.querySelector('.loading');
    if (spinner) {
        button.removeChild(spinner);
    }
}

// Генерация изображений
document.getElementById('generate-btn').addEventListener('click', function() {
    showLoading('generate-btn');
    
    const size = document.getElementById('image-size').value;
    const mean = document.getElementById('mean').value;
    const sigma = document.getElementById('sigma').value;
    
    fetch('/generate_images', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            size: size,
            mean: mean,
            sigma: sigma
        })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('generated-images').src = 'data:image/png;base64,' + data.image;
        document.getElementById('ssim-value').textContent = data.ssim;
        document.getElementById('images-container').style.display = 'block';
        
        // Сохраняем данные для последующего использования
        imageData.phantom = data.phantom;
        imageData.noisePhantom = data.noisePhantom;
        
        hideLoading('generate-btn');
        
        // Прокрутка к контейнеру с изображениями
        document.getElementById('images-container').scrollIntoView({ behavior: 'smooth' });
    })
    .catch(error => {
        console.error('Ошибка:', error);
        hideLoading('generate-btn');
        alert('Произошла ошибка при генерации изображений. Проверьте консоль для подробностей.');
    });
});

// Преобразование Радона
document.getElementById('radon-btn').addEventListener('click', function() {
    showLoading('radon-btn');
    
    fetch('/radon_transform', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            phantom: imageData.phantom,
            noisePhantom: imageData.noisePhantom
        })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('radon-original').src = 'data:image/png;base64,' + data.radon1;
        document.getElementById('radon-noisy').src = 'data:image/png;base64,' + data.radon2;
        document.getElementById('radon-container').style.display = 'block';
        
        // Сохраняем данные для последующего использования
        imageData.r1 = data.r1;
        imageData.r2 = data.r2;
        
        hideLoading('radon-btn');
        
        // Прокрутка к контейнеру преобразования Радона
        document.getElementById('radon-container').scrollIntoView({ behavior: 'smooth' });
    })
    .catch(error => {
        console.error('Ошибка:', error);
        hideLoading('radon-btn');
        alert('Произошла ошибка при выполнении преобразования Радона. Проверьте консоль для подробностей.');
    });
});

// Анализ срезов
document.getElementById('slice-btn').addEventListener('click', function() {
    showLoading('slice-btn');
    
    const angle = document.getElementById('angle').value;
    
    fetch('/slice_analysis', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            r1: imageData.r1,
            r2: imageData.r2,
            angle: angle
        })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('slices-img').src = 'data:image/png;base64,' + data.slices;
        document.getElementById('spectrum-img').src = 'data:image/png;base64,' + data.spectrum;
        document.getElementById('slice-container').style.display = 'block';
        
        hideLoading('slice-btn');
        
        // Прокрутка к контейнеру анализа срезов
        document.getElementById('slice-container').scrollIntoView({ behavior: 'smooth' });
    })
    .catch(error => {
        console.error('Ошибка:', error);
        hideLoading('slice-btn');
        alert('Произошла ошибка при анализе срезов. Проверьте консоль для подробностей.');
    });
});

// Анализ двумерного спектра
document.getElementById('spectrum-2d-btn').addEventListener('click', function() {
    showLoading('spectrum-2d-btn');

    fetch('/spectrum_2d', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            phantom: imageData.phantom,
            noisePhantom: imageData.noisePhantom,
            diameter: document.getElementById('diameter').value
        })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('filter-img').src = 'data:image/png;base64,' + data.lowpass;
        document.getElementById('spectrum-2d-container').style.display = 'block';

        hideLoading('spectrum-2d-btn');

        // Прокрутка к контейнеру двумерного спектра
        document.getElementById('spectrum-2d-container').scrollIntoView({ behavior: 'smooth' });
    })
    .catch(error => {
        console.error('Ошибка:', error);
        hideLoading('spectrum-2d-btn');
        alert('Произошла ошибка при анализе двумерного спектра. Проверьте консоль для подробностей.');
    });
});

// Применение фильтра с новым диаметром
document.getElementById('apply-filter-btn').addEventListener('click', function() {
    showLoading('apply-filter-btn');
    
    fetch('/spectrum_2d', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            phantom: imageData.phantom,
            noisePhantom: imageData.noisePhantom,
            diameter: document.getElementById('diameter').value
        })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('filter-img').src = 'data:image/png;base64,' + data.lowpass;
        
        hideLoading('apply-filter-btn');
    })
    .catch(error => {
        console.error('Ошибка:', error);
        hideLoading('apply-filter-btn');
        alert('Произошла ошибка при применении фильтра. Проверьте консоль для подробностей.');
    });
});

// Переход к анализу SSIM
document.getElementById('ssim-analysis-btn').addEventListener('click', function() {
    document.getElementById('ssim-container').style.display = 'block';
    document.getElementById('ssim-container').scrollIntoView({ behavior: 'smooth' });
});

// Запуск анализа SSIM
document.getElementById('run-ssim-analysis-btn').addEventListener('click', function() {
    showLoading('run-ssim-analysis-btn');

    const numImages = document.getElementById('num-images').value;
    const m = document.getElementById('m-value').value;
    const s = document.getElementById('s-value').value;
    const sigmaStep = document.getElementById('sigma-step').value;
    const size = document.getElementById('image-size').value;

    console.log("Отправка данных на сервер:", {  // Debug log
        numOfImages: numImages,
        m: m,
        s: s,
        sigma_step: sigmaStep,
        size: size
    });

    fetch('/ssim_analysis', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            numOfImages: numImages,
            m: m,
            s: s,
            sigma_step: sigmaStep,
            size: size
        })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('ssim-table').innerHTML = data.table;
        document.getElementById('ssim-results').style.display = 'block';
        
        hideLoading('run-ssim-analysis-btn');
        
        // Прокрутка к результатам
        document.getElementById('ssim-results').scrollIntoView({ behavior: 'smooth' });
    })
    .catch(error => {
        console.error('Ошибка:', error);
        hideLoading('run-ssim-analysis-btn');
        alert('Произошла ошибка при анализе SSIM. Проверьте консоль для подробностей.');
    });
});