import os
import copy
from PIL import Image
import cv2
import skimage.exposure
import numpy as np
import torch
import time

from color_helper import calc_delta_CIEDE2000
from dino import Dino
from sam import SAM
from fsam import FSAM


DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
DEVICE = "cpu"
GD_FILENAME = "./models/groundingdino_swint_ogc.pth"
GD_CONFIG_FILENAME = "./models/GroundingDINO_SwinT_OGC.py"
SAM_FILENAME = "./models/sam_vit_h_4b8939.pth"
SAM_TYPE = "vit_h"
FSAM_FILENAME = "./models/FastSAM.pt"

# hyper-param for GroundingDINO
CAPTION = "wall"
BOX_THRESHOLD = 0.30
TEXT_THRESHOLD = 0.35

# Parameter for Mask Bucketing
MAX_DELTA = 30

# hyper-param for FastSAM
IOU_THRESHOLD = 0.9
MASK_THRESHOLD = 0.45


class Singleton:
    """
    A non-thread-safe helper class to ease implementing singletons.
    This should be used as a decorator -- not a metaclass -- to the
    class that should be a singleton.

    The decorated class can define one `__init__` function that
    takes only the `self` argument. Also, the decorated class cannot be
    inherited from. Other than that, there are no restrictions that apply
    to the decorated class.

    To get the singleton instance, use the `instance` method. Trying
    to use `__call__` will result in a `TypeError` being raised.

    """

    def __init__(self, decorated):
        self._decorated = decorated

    def instance(self):
        """
        Returns the singleton instance. Upon its first call, it creates a
        new instance of the decorated class and calls its `__init__` method.
        On all subsequent calls, the already created instance is returned.

        """
        try:
            return self._instance
        except AttributeError:
            self._instance = self._decorated()
            return self._instance

    def __call__(self):
        raise TypeError("Singletons must be accessed through `instance()`.")

    def __instancecheck__(self, inst):
        return isinstance(inst, self._decorated)


@Singleton
class DinoSAMSingleton:
    def __init__(self):
        self.gd_predictor = Dino(GD_FILENAME, GD_CONFIG_FILENAME, DEVICE)
        print("GroundingDINO Model Loaded")
        self.sam_predictor = SAM(SAM_FILENAME, SAM_TYPE, "cuda")
        print("SAM Model Loaded")
        self.fsam_predictor = FSAM(FSAM_FILENAME, DEVICE, MASK_THRESHOLD, IOU_THRESHOLD)
        print("FastSAM Model Loaded")

    def run_pipeline(self, image_path, color):
        print(f"=== Starting Grounded SAM Pipeline for Image {image_path} ===\n")
        image_pil = Image.open(image_path).convert("RGB")  # load image

        pred_dict = self.gd_predictor.run_inference(
            image_pil, CAPTION, BOX_THRESHOLD, TEXT_THRESHOLD
        )
        masks = self.sam_predictor.run_inference(image_pil, pred_dict)

        boxed_image = self.gd_predictor.apply_boxes_to_image(image_pil, pred_dict)
        boxed_image.save(
            f"{os.path.splitext(os.path.basename(image_path))[0]}_boxed.jpg"
        )
        masked_image = self.sam_predictor.apply_mask_to_image(image_pil, masks)
        masked_image.save(
            f"{os.path.splitext(os.path.basename(image_path))[0]}_mask.jpg"
        )

        print("\n=== Starting Image Recoloring ===\n")
        image_cv = cv2.imread(image_path)
        buckets = self.create_buckets(image_cv, masks)
        print(buckets)

        masks = self.merge_masks(buckets, masks)
        masked_image = self.sam_predictor.apply_mask_to_image(image_pil, masks)
        masked_image.save(
            f"{os.path.splitext(os.path.basename(image_path))[0]}_mask_merged.jpg"
        )

        recolored_image = self.recolor(image_cv, color, masks)
        cv2.imwrite(
            f"{os.path.splitext(os.path.basename(image_path))[0]}_recolored.png",
            recolored_image,
        )

        print("\n=== Pipeline Finished ===\n")

    def run_pipeline_fsam(self, image_path, color):
        print(f"=== Starting Grounded FSAM Pipeline for Image {image_path} ===\n")
        image_pil = Image.open(image_path).convert("RGB")  # load image

        pred_dict = self.gd_predictor.run_inference(
            image_pil, CAPTION, BOX_THRESHOLD, TEXT_THRESHOLD
        )
        masks = self.fsam_predictor.run_inference(image_pil, pred_dict)

        boxed_image = self.gd_predictor.apply_boxes_to_image(image_pil, pred_dict)
        boxed_image.save(
            f"{os.path.splitext(os.path.basename(image_path))[0]}_boxed_fsam.jpg"
        )
        masked_image = self.fsam_predictor.apply_mask_to_image(image_pil, masks)
        cv2.imwrite(
            f"{os.path.splitext(os.path.basename(image_path))[0]}_mask_fsam.jpg",
            masked_image,
        )

        print("\n=== Starting Image Recoloring ===\n")
        image_cv = cv2.imread(image_path)
        recolored_image = self.recolor(image_cv, color, masks)
        cv2.imwrite(
            f"{os.path.splitext(os.path.basename(image_path))[0]}_recolored_fsam.png",
            recolored_image,
        )

        print("\n=== Pipeline Finished ===\n")

    def create_buckets(self, image_cv, masks):
        buckets = {}

        image_lab = cv2.cvtColor(image_cv, cv2.COLOR_BGR2LAB)

        for i in range(len(masks)):
            mask = (masks[i].astype(np.uint8) * 255).astype(np.uint8)
            ave_color = cv2.mean(image_lab, mask=mask)[:3]

            if not buckets:
                buckets[len(buckets) + 1] = {"avg": list(ave_color), "masks": [i]}
            else:
                smallest_delta = float("inf")
                best_bucket = -1

                for key in buckets.keys():
                    ave_bucket_color = buckets[key]["avg"]
                    distance = calc_delta_CIEDE2000(ave_bucket_color, ave_color)
                    if distance < smallest_delta:
                        smallest_delta = distance
                        best_bucket = key

                if best_bucket != -1:
                    if smallest_delta > MAX_DELTA:
                        buckets[len(buckets) + 1] = {
                            "avg": list(ave_color),
                            "masks": [i],
                        }
                    else:
                        buckets[key]["avg"] = np.mean(
                            np.array([buckets[key]["avg"], ave_color]), axis=0
                        ).tolist()
                        buckets[key]["masks"].append(i)
        return buckets

    def merge_masks(self, buckets, masks):
        new_masks = []

        for key in buckets.keys():
            mask_list = buckets[key]["masks"]
            new_mask = None
            for index in mask_list:
                if new_mask is None:
                    new_mask = masks[index]
                else:
                    new_mask = np.logical_or(new_mask, masks[index])
            new_masks.append(new_mask)
        return new_masks

    def recolor(self, image_cv, color_rgb, masks):
        image = copy.deepcopy(image_cv).astype(np.int16)
        color_bgr = color_rgb[::-1]
        desired_color = np.asarray(color_bgr, dtype=np.float64)

        for wallmask in masks:
            mask = (wallmask.astype(np.uint8) * 255).astype(np.uint8)

            # get average bgr color of masked section
            ave_color = cv2.mean(image, mask=mask)[:3]
            print(f"Average color = {ave_color}")

            # compute difference colors and make into an image the same size as input
            diff_color = desired_color - ave_color
            diff_color = np.full_like(image, diff_color, dtype=np.int16)

            # shift input image color
            # cv2.add clips automatically
            new_image = cv2.add(image, diff_color)

            # antialias mask, convert to float in range 0 to 1 and make 3-channels
            mask = cv2.GaussianBlur(
                mask, (0, 0), sigmaX=3, sigmaY=3, borderType=cv2.BORDER_DEFAULT
            )
            mask = skimage.exposure.rescale_intensity(
                mask, in_range=(100, 150), out_range=(0, 1)
            ).astype(np.float32)
            mask = cv2.merge([mask, mask, mask])

            # combine img and new_img using mask
            result = image * (1 - mask) + new_image * mask
            result = result.clip(0, 255).astype(np.int16)
            image = result

        return image


if __name__ == "__main__":
    print("Running pipeline test")

    dir_path = os.path.dirname(os.path.realpath(__file__))

    # PPG "Viva La Bleu"
    # "PPG1242-3"
    color = [151, 190, 226]  # rgb

    # # Benjamin Moore "Grape Green"
    # # "2027-40"
    # color = [213, 216, 105]  # rgb

    start = time.time()
    inst1 = DinoSAMSingleton.instance()
    end = time.time()
    print(f"Loading models took {end-start} seconds!")
    # image1 = os.path.join(dir_path, "tests/img.jpg")
    # inst1.run_pipeline(image1, color)

    inst2 = DinoSAMSingleton.instance()
    image2 = os.path.join(dir_path, "tests/IMG_9084.JPG")
    start = time.time()
    inst2.run_pipeline(image2, color)
    end = time.time()
    print(f"Grounded SAM Pipeline took {end-start} seconds!")
