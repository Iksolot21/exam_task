import cv2
import math
import numpy as np
import matplotlib.pyplot as plt
from skimage import transform, metrics
from phantominator import shepp_logan
from scipy.signal import savgol_filter

def showImages(*args, titles=None):
    """
    Функция для вывода изображений на экран, выводит переданные изображения в строку.
    """
    if titles is None:
        titles = []

    fig, axes = plt.subplots(1, len(args))

    if len(args) == 1:
        axes = [axes]

    for i in range(len(axes)):
        axes[i].imshow(args[i], cmap="gray")
        if len(titles) != 0:
            axes[i].set_title(titles[i], fontsize='14')

    fig.set_figwidth(12)
    fig.set_figheight(12)
    return fig

def createTestImage(size, output=False):
    """
    Функция генерации тестового изображения.
    """
    ph = shepp_logan(size)
    image = transform.rotate(ph, 180)
    if output:
        fig, ax = plt.subplots(1, figsize=(6, 6))
        ax.set_title(f"Исходное изображение\n({size}x{size}) px", fontsize='14')
        ax.imshow(image, cmap='gray')
    return image

def addGaussianNoise(image, mean, sigma):
    """
    Функция для добавления шума Гаусса в тестовое изображение.
    """
    gauss = np.random.normal(mean, sigma, image.shape)
    gauss = gauss.reshape(image.shape)
    noisy = image + gauss
    return noisy

def radonTransformation(image, min_theta=0, max_theta=180, output=False):
    """
    Функция преобразования Радона.
    """
    theta = np.arange(min_theta, max_theta+1)
    sinogram = transform.radon(image, theta=theta)

    if output:
        dx, dy = 0.5 * 180.0 / max(image.shape), 0.5 / sinogram.shape[0]
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 5.5))

        ax1.set_title(f"Исходное изображение\n({image.shape[0]}x{image.shape[1]}) px", fontsize='14')
        ax1.imshow(image, cmap=plt.cm.Greys_r)
        ax1.axis("off")

        ax2.set_title("Преобразование Радона\n(Sinogram)", fontsize='14')
        ax2.set_xlabel("Угол (deg)", fontsize='14')
        ax2.set_ylabel("Расположение датчиков (pixels)", fontsize='14')

        ax2.imshow(sinogram, cmap=plt.cm.Greys_r,
                   extent=(-dx, 180.0 + dx, -dy, sinogram.shape[0] + dy),
                   aspect='auto')

        fig.tight_layout()
    return sinogram

def spectrum(vector):
    """
    Функция для расчета спектра среза изображения с помощью преобразования Фурье
    """
    spec = np.fft.fft(vector)
    spec = np.log(1 + np.abs(spec))
    return spec

def spectrum_2dim(image):
    """
    Функция для получения двумерного Фурье спектра изображения
    """
    fft2 = np.fft.fft2(image)
    center = np.fft.fftshift(fft2)
    return center

def distance(point1, point2):
    """
    Расстояние между двумя точками
    """
    return math.sqrt((point1[0]-point2[0])**2 + (point1[1]-point2[1])**2)

def ideal_HighPass_filter(spectrum, D0):
    """
    Идеальный высокочастотный фильтр
    """
    imgShape = spectrum.shape
    base = np.ones(imgShape[:2])
    rows, cols = imgShape[:2]
    center = (rows/2, cols/2)
    for x in range(cols):
        for y in range(rows):
            if distance((y,x), center) < D0:
                base[y,x] = 0
    return base * spectrum

def ideal_LowPass_filter(spectrum, D0):
    """
    Идеальный низкочастотный фильтр
    """
    imgShape = spectrum.shape
    base = np.zeros(imgShape[:2])
    rows, cols = imgShape[:2]
    center = (rows/2, cols/2)
    for x in range(cols):
        for y in range(rows):
            if distance((y,x), center) < D0:
                base[y,x] = 1
    #return base * spectrum
    return base * spectrum # Keep as complex for correct SSIM