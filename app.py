from flask import Flask, render_template, request, jsonify
import io
import base64
import numpy as np
import matplotlib.pyplot as plt
from skimage import metrics
from prettytable import PrettyTable
from utils.image_processing import (
    createTestImage, addGaussianNoise, radonTransformation,
    spectrum, spectrum_2dim, ideal_LowPass_filter
)

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

def fig_to_base64(fig):
    """Преобразует фигуру matplotlib в строку base64 для отображения в HTML"""
    img_buf = io.BytesIO()
    fig.savefig(img_buf, format='png', bbox_inches='tight')
    img_buf.seek(0)
    img_str = base64.b64encode(img_buf.read()).decode('utf-8')
    return img_str

@app.route('/generate_images', methods=['POST'])
def generate_images():
    try:
        data = request.get_json()

        size = int(data.get('size', 500))
        mean = float(data.get('mean', 0.01))
        sigma = float(data.get('sigma', 0.04))

        # Генерация изображений
        phantom = createTestImage(size)
        noisePhantom = addGaussianNoise(phantom, mean, sigma)
        noisePhantom = np.clip(noisePhantom, 0, 1)

        # Создание и сохранение изображений для отображения
        fig, axes = plt.subplots(1, 2, figsize=(12, 6))
        axes[0].imshow(phantom, cmap="gray")
        axes[0].set_title("Исходное", fontsize='14')
        axes[1].imshow(noisePhantom, cmap="gray")
        axes[1].set_title("Зашумленное", fontsize='14')

        img_str = fig_to_base64(fig)
        plt.close(fig)

        ssim = round(metrics.structural_similarity(phantom, noisePhantom, multichannel=True, data_range=1.0), 4)

        # Преобразуем в float32 для передачи в JSON
        phantom = phantom.astype(np.float32)
        noisePhantom = noisePhantom.astype(np.float32)

        return jsonify({
            'image': img_str,
            'ssim': ssim,
            'phantom': phantom.tolist(),
            'noisePhantom': noisePhantom.tolist()
        })
    except Exception as e:
        print(e)  # Log the exception
        return jsonify({'error': str(e)}), 500

@app.route('/radon_transform', methods=['POST'])
def radon_transform():
    try:
        data = request.get_json()

        phantom = np.array(data.get('phantom', []), dtype=np.float32)
        noisePhantom = np.array(data.get('noisePhantom', []), dtype=np.float32)

        # Преобразование Радона
        r1 = radonTransformation(phantom)
        r2 = radonTransformation(noisePhantom)

        # Создание визуализации преобразования Радона
        fig1, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
        ax1.set_title("Исходное изображение", fontsize='14')
        ax1.imshow(phantom, cmap=plt.cm.Greys_r)
        ax1.axis("off")

        dx, dy = 0.5 * 180.0 / max(phantom.shape), 0.5 / r1.shape[0]
        ax2.set_title("Преобразование Радона (Sinogram)", fontsize='14')
        ax2.set_xlabel("Угол (deg)", fontsize='14')
        ax2.set_ylabel("Расположение датчиков (pixels)", fontsize='14')
        ax2.imshow(r1, cmap=plt.cm.Greys_r,
                extent=(-dx, 180.0 + dx, -dy, r1.shape[0] + dy),
                aspect='auto')

        img_str1 = fig_to_base64(fig1)
        plt.close(fig1)

        fig2, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
        ax1.set_title("Зашумленное изображение", fontsize='14')
        ax1.imshow(noisePhantom, cmap=plt.cm.Greys_r)
        ax1.axis("off")

        dx, dy = 0.5 * 180.0 / max(noisePhantom.shape), 0.5 / r2.shape[0]
        ax2.set_title("Преобразование Радона (Sinogram)", fontsize='14')
        ax2.set_xlabel("Угол (deg)", fontsize='14')
        ax2.set_ylabel("Расположение датчиков (pixels)", fontsize='14')
        ax2.imshow(r2, cmap=plt.cm.Greys_r,
                extent=(-dx, 180.0 + dx, -dy, r2.shape[0] + dy),
                aspect='auto')

        img_str2 = fig_to_base64(fig2)
        plt.close(fig2)

        # Преобразуем в float32 для передачи в JSON
        r1 = r1.astype(np.float32)
        r2 = r2.astype(np.float32)

        return jsonify({
            'radon1': img_str1,
            'radon2': img_str2,
            'r1': r1.tolist(),
            'r2': r2.tolist()
        })
    except Exception as e:
        print(e)  # Log the exception
        return jsonify({'error': str(e)}), 500

@app.route('/slice_analysis', methods=['POST'])
def slice_analysis():
    try:
        data = request.get_json()

        r1 = np.array(data.get('r1', []), dtype=np.float32)
        r2 = np.array(data.get('r2', []), dtype=np.float32)
        angle = int(data.get('angle', 85))

        # Получаем срез
        x = np.arange(len(r1))
        x = x/max(x)

        slice_r1 = r1[:, angle]
        slice_r2 = r2[:, angle]

        # Визуализируем срезы
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

        ax1.set_title(f"Cрез {angle}° для исходного изображения", fontsize='14')
        ax1.plot(x, slice_r1, linewidth='1', color='#27a841')
        ax1.grid()

        ax2.set_title(f"Cрез {angle}° для зашумленного изображения", fontsize='14')
        ax2.plot(x, slice_r2, linewidth='1', color='#27a841')
        ax2.grid()

        img_str = fig_to_base64(fig)
        plt.close(fig)

        # Расчет спектров
        spec_r1 = spectrum(slice_r1)
        spec_r2 = spectrum(slice_r2)

        fig2, ax = plt.subplots(figsize=(12, 4))

        ax.set_xlabel("Частота, циклов на пиксель", fontsize=14)
        ax.set_ylabel("Амплитуда", fontsize=14)
        ax.set_title("Сопоставительный анализ спектров", fontsize=15)

        ax.plot(x[:len(x)//2], spec_r1[:len(spec_r1)//2],
                color='#707060',
                label="Спектр исходного изображения",
                linewidth='1',
                linestyle='--'
        )
        ax.plot(x[:len(x)//2], spec_r2[:len(spec_r2)//2],
                color='orange',
                label="Спектр зашумленного изображения",
                linewidth='1'
        )
        ax.legend()
        ax.grid()

        spectrum_img = fig_to_base64(fig2)
        plt.close(fig2)

        return jsonify({
            'slices': img_str,
            'spectrum': spectrum_img
        })
    except Exception as e:
        print(e)  # Log the exception
        return jsonify({'error': str(e)}), 500

@app.route('/spectrum_2d', methods=['POST'])
def spectrum_2d_analysis():
    try:
        data = request.get_json()

        phantom = np.array(data.get('phantom', []), dtype=np.float32)
        noisePhantom = np.array(data.get('noisePhantom', []), dtype=np.float32)

        # Рассчитываем 2D спектры
        sp_phantom = np.log(1 + np.abs(spectrum_2dim(phantom)))
        sp_noisePhantom = np.log(1 + np.abs(spectrum_2dim(noisePhantom)))

        # Низкочастотный фильтр
        diameter = int(data.get('diameter', 60))
        lp_img1 = ideal_LowPass_filter(sp_phantom, diameter)
        lp_img2 = ideal_LowPass_filter(sp_noisePhantom, diameter)

        # Вычисление SSIM (важно: используем np.abs для комплексных чисел)
        data_range = np.max([np.max(np.abs(lp_img1)), np.max(np.abs(lp_img2))])
        ssim = round(metrics.structural_similarity(np.abs(lp_img1), np.abs(lp_img2), multichannel=True, data_range=data_range), 4)

        # Визуализация 2D спектров и отфильтрованных изображений
        fig, axes = plt.subplots(1, 2, figsize=(12, 6))

        axes[0].imshow(np.abs(lp_img1), cmap="gray")  # np.abs для отображения
        axes[0].set_title(f"НЧ фильтр исходного (D={diameter}, SSIM={ssim})", fontsize='14')

        axes[1].imshow(np.abs(lp_img2), cmap="gray")  # np.abs для отображения
        axes[1].set_title(f"НЧ фильтр зашумленного (D={diameter}, SSIM={ssim})", fontsize='14')

        img_str = fig_to_base64(fig)
        plt.close(fig)

        return jsonify({
            'spectrum2d': img_str, # fix: теперь содержит и спектры и отфильтрованные
            'lowpass': img_str, #  а также ssim
        })
    except Exception as e:
        print(f"Error in /spectrum_2d: {e}")  # Дополнительное логирование
        return jsonify({'error': str(e)}), 500

@app.route('/ssim_analysis', methods=['POST'])
def ssim_analysis():
    try:
        data = request.get_json()

        num_images = int(data.get('numOfImages', 10))
        m = float(data.get('m', 0.01))
        s = float(data.get('s', 0))
        sigma_step = float(data.get('sigma_step', 0.05))

        size = int(data.get('size', 500))

        print(f"Начало анализа SSIM: num_images={num_images}, m={m}, s={s}, sigma_step={sigma_step}, size={size}") # Log

        # Генерация изображений и анализ SSIM
        phantom = createTestImage(size)
        defSpectrum = np.log(1 + np.abs(spectrum_2dim(phantom)))

        # Подготовка таблицы и данных
        table = PrettyTable()
        table.field_names = ["№", "Мат.ожидание", "Дисперсия", "SSIM c исходным", "Диаметр среза", "SSIM по срезу"]

        results = []
        current_s = s

        for i in range(num_images):
            print(f"Итерация {i+1}/{num_images}, current_s={current_s}") # Log

            img = addGaussianNoise(phantom, m, current_s)
            img = np.clip(img, 0, 1)

            imgSSIM = round(metrics.structural_similarity(phantom, img, multichannel=True, data_range=1.0), 4)
            noiseSpectrum = np.log(1 + np.abs(spectrum_2dim(img)))

            diameter_results = []
            for diameter in range(1, 162, 1):
                lp_img1 = ideal_LowPass_filter(defSpectrum, diameter)
                lp_img2 = ideal_LowPass_filter(noiseSpectrum, diameter)

                # Вычисление SSIM с учетом комплексных чисел и динамического диапазона
                data_range = np.max([np.max(np.abs(lp_img1)), np.max(np.abs(lp_img2))])
                sp_ssim = round(metrics.structural_similarity(np.abs(lp_img1), np.abs(lp_img2), multichannel=True, data_range=data_range), 4)


                diameter_results.append({
                    'diameter': diameter,
                    'ssim': sp_ssim
                })

                # Добавляем в таблицу только некоторые значения для наглядности
                if diameter % 10 == 0 or diameter == 1:
                    if diameter == 1:
                        table.add_row([i+1, m, current_s, imgSSIM, diameter, sp_ssim])
                    else:
                        table.add_row(["", "", "", "", diameter, sp_ssim])

            if i < num_images - 1:
                table.add_row(["------", "------", "------", "------", "------", "------"])

            results.append({
                'index': i+1,
                'mean': m,
                'sigma': current_s,
                'imageSSIM': imgSSIM,
                'diameters': diameter_results
            })

            current_s = round(current_s + sigma_step, 3)

        print("Анализ SSIM завершен успешно") # Log

        return jsonify({
            'table': table.get_html_string(),
            'results': results
        })
    except Exception as e:
        print(f"Error in /ssim_analysis: {e}")  # Log the exception
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)