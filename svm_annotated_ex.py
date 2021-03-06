import cv2
import random
import os.path as osp
import numpy as np
import pickle
from sklearn.svm import SVC
from sklearn.metrics import classification_report
from sklearn.preprocessing import minmax_scale
from sklearn.ensemble import RandomForestClassifier

train_dir = '../exudates_data/train'
test_dir = '../exudates_data/test'
mask_dir = '../exudates/ex_masks'


def is_background_point_considerable(x, y, mask):
    return np.sum(mask[y-5: y+5, x-5:x+5]) < 15


def read_annotations(directory, index):
    annotations = []
    with open(osp.join(directory, 'annotations', index.split(".")[0] + '.txt')) as annotation:
        for entry in annotation:
            data = entry.strip().split()
            rect = map(int, data[1:])
            annotations.append(rect)
    return annotations


def read_image(directory, index):
    img = cv2.imread(osp.join(directory, 'images', index))  # Read image
    if img is None:
        print "Directory is not valid: {}".format(osp.join(directory, 'images', index + '.png'))
    img = cv2.GaussianBlur(img, (3, 3), 1)  # Apply Gaussian blur
    img = img[:, :, 1]  # Green channel BGR
    return img


def read_image_names(directory):
    with open(osp.join(directory, 'list')) as f:
        lines = f.readlines()
        return [l.strip() for l in lines]


def read_data(directory):
    x, y = [], []
    # Load image names
    image_names = read_image_names(directory)
    for image_name in image_names:
        # Get annotation for image
        annotations = read_annotations(directory, image_name)
        # Get image
        image = read_image(directory, image_name)

        # Load positive samples
        for annotation in annotations:
            # Crop region based on annotation
            region = image[annotation[1]:annotation[3], annotation[0]:annotation[2]]
            # Calculate histogram for that region
            hist = cv2.calcHist([region], [0], None, [256], [0, 256])
            # Add histogram to data and label
            hist = hist.reshape(-1)/(region.shape[0] * region.shape[1])
            x.append(hist)
            y.append(1)

        # Load negative samples
        image_basename = osp.basename(image_name)
        mask = cv2.imread(osp.join(mask_dir, image_basename), 0)

        negative_samples_size = len(annotations)
        for _ in range(negative_samples_size):
            got_point = False
            for ___ in range(5):
                # Choose random point
                p1 = random.randint(11, image.shape[1] - 12)
                p2 = random.randint(11, image.shape[0] - 12)

                if is_background_point_considerable(p1, p2, mask) and image[p2, p1] > 10:
                    got_point = True
                    break

            if got_point:
                region = image[p2-5: p2+5, p1-5:p1+5]
                hist = cv2.calcHist([region], [0], None, [256], [0, 256])
                x.append(hist.reshape(-1))
                y.append(0)

    return x, y


def load_data():
    # Load train data
    x_train, y_train = read_data(train_dir)

    # Load test data
    x_test, y_test = read_data(test_dir)

    return x_train, y_train, x_test, y_test


def train_rf():
    # Define model
    rf = RandomForestClassifier(n_estimators=256)
    # Load data
    x_train, y_train, x_test, y_test = load_data()
    # Train model
    rf.fit(x_train, y_train)
    # Predict on test data
    y_pred = rf.predict(x_test)

    print classification_report(y_test, y_pred)

    pickle.dump(rf, open('rf_model.pkl', 'wb'))


def train_svm():
    # Define model
    svm = SVC(kernel='poly', degree=2)
    # Load data
    x_train, y_train, x_test, y_test = load_data()
    # Train model
    svm.fit(x_train, y_train)
    # Predict on test data
    y_pred = svm.predict(x_test)

    print classification_report(y_test, y_pred)

    pickle.dump(svm, open('svm_model.pkl', 'wb'))


def train_and_evaluate_model():
    # train_svm()
    train_rf()
    # from sklearn.manifold import TSNE
    # model = TSNE(n_components=2, random_state=0)
    # pos = model.fit_transform(x_train)
    # import matplotlib.pyplot as plt
    # plt.figure(1)
    # y_train = np.array(y_train)
    # plt.scatter(pos[y_train == 1, 0], pos[y_train == 1, 1], marker='o', color='b')
    # plt.scatter(pos[y_train == 0, 0], pos[y_train == 0, 1], marker='o', color='g')
    # plt.title('Exudate -- blue, background -- green')
    # plt.savefig('tsne_vis.png')
    # plt.show()


def get_descriptor(region):
    hist = cv2.calcHist([region], [0], None, [256], [0, 256])
    # desc = minmax_scale(hist.reshape(-1))
    desc = hist.reshape(-1)/(region.shape[0] * region.shape[1])
    return desc


def prediction(region, model):
    result = model.predict(get_descriptor(region))
    return result

if __name__ == '__main__':
    train_and_evaluate_model()
