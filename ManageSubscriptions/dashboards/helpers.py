import secrets,hashlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.interpolate import make_interp_spline
import numpy as np
from PIL import Image


def generate_usage_chart(data):
    x = np.array(data['dates'])
    y = np.array(data['requests'])

    x_numeric = np.arange(len(x))

    plt.figure(figsize=(9, 3))

    if len(x) > 3:
        x_new = np.linspace(x_numeric.min(), x_numeric.max(), 300)
        spline = make_interp_spline(x_numeric, y, k=3)
        y_smooth = spline(x_new)
        plt.plot(x_new, y_smooth, color='#8E65E0', linewidth=2)
        for i in range(len(x_new)-1):
            alpha = 1 - (i / len(x_new))
            plt.fill_between(x_new[i:i+2], y_smooth[i:i+2], color='#8E65E0', alpha=alpha * 0.3)
    else:
        plt.plot(x_numeric, y, marker='o', color='#8E65E0', linewidth=2)

    plt.title("", fontsize=16, color='white')
    plt.xlabel("", color='white')
    plt.ylabel("", color='white')
    plt.xticks(ticks=x_numeric, labels=x, rotation=45, color='white')
    plt.yticks(color='white')
    plt.grid(True, color='#555', linestyle='--', alpha=0.3)
    plt.gca().set_facecolor('#0A0F1C')
    plt.gcf().set_facecolor('#0A0F1C')

    filename = secrets.token_hex(24) + '.png'
    filepath = f'ManageSubscriptions/static/usage_logs/{filename}'
    plt.tight_layout()
    plt.savefig(filepath, transparent=True)
    plt.close()
    return filename

def calc_file_hash(fileData):
    hasher = hashlib.md5()
    with open(fileData, 'rb') as file:
        buf = file.read()
        hasher.update(buf)
    return hasher.hexdigest()

def check_image_security(image):
    try:
        img = Image.open(image)
        img.verify()
        image.seek(0)
        return True
    except:
        return False
