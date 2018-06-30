import os
import cv2
import random
import pickle

from PIL import Image, ImageFilter

from computer_text_generator import ComputerTextGenerator
# try:
#     from .handwritten_text_generator import HandwrittenTextGenerator
# except ImportError as e:
#     print('Missing modules for handwritten text generation.')
from background_generator import BackgroundGenerator
from distorsion_generator import DistorsionGenerator

class FakeTextDataGenerator(object):
    
    @classmethod
    def createTextPicture(cls, is_handwritten, text, font, text_color, skewing_angle, random_skew):
        ##########################
        # Create picture of text #
        ##########################
        if is_handwritten:
            image = HandwrittenTextGenerator.generate(text)
        else:
            image = ComputerTextGenerator.generate(text, font, text_color)

        random_angle = random.randint(0-skewing_angle, skewing_angle)

        rotated_img = image.rotate(skewing_angle if not random_skew else random_angle, expand=1)
        
        return rotated_img

    @classmethod
    def applyDistorsion(cls, rotated_img, distorsion_type, distorsion_orientation):
        #############################
        # Apply distorsion to image #
        #############################
        if distorsion_type == 0:
            distorted_img = rotated_img # Mind = blown
        elif distorsion_type == 1:
            distorted_img = DistorsionGenerator.sin(
                rotated_img,
                vertical=(distorsion_orientation == 0 or distorsion_orientation == 2),
                horizontal=(distorsion_orientation == 1 or distorsion_orientation == 2)
            )
        elif distorsion_type == 2:
            distorted_img = DistorsionGenerator.cos(
                rotated_img,
                vertical=(distorsion_orientation == 0 or distorsion_orientation == 2),
                horizontal=(distorsion_orientation == 1 or distorsion_orientation == 2)
            )
        else:
            distorted_img = DistorsionGenerator.random(
                rotated_img,
                vertical=(distorsion_orientation == 0 or distorsion_orientation == 2),
                horizontal=(distorsion_orientation == 1 or distorsion_orientation == 2)
            )
        
        return distorted_img

    @classmethod
    def generateBackgroundImage(cls, distorted_img_list, background_type):
        #############################
        # Generate background image #
        #############################
#         new_text_width, new_text_height = distorted_img.size
        background_width = random.randint(400, 800)
        background_height = random.randint(300, 500)
        
        bb_list = []
        subtext_height = [background_height/6.0, background_height/2.0, 5*background_height/6.0]
        subtext_width = [background_width/8.0, 3 * background_width/8.0, 5*background_width/8.0]
        
        if background_type == 0:
            background = BackgroundGenerator.gaussian_noise( background_height, background_width)
        elif background_type == 1:
            background = BackgroundGenerator.plain_white( background_height, background_width)
        elif background_type == 2:
            background = BackgroundGenerator.quasicrystal( background_height, background_width)
        else:
            background = BackgroundGenerator.picture( background_height, background_width)
        
        ##TO-DO : NEEDS ENTIRE WORK ON ADDING DIFFERENT WORDS TO THE IMAGE
        for word_index in range(9):
            distorted_img = distorted_img_list[word_index]
            bb_width, bb_height = distorted_img.size
            bb_xmin = int(subtext_width[word_index % 3])
            bb_ymin = int(subtext_height[int(word_index/ 3.0)])
            bb_list.append([bb_xmin, bb_ymin, bb_xmin + bb_width, bb_ymin + bb_height])
            
            mask = distorted_img.point(lambda x: 0 if x == 255 or x == 0 else 255, '1')
            background.paste(distorted_img, ( bb_xmin, bb_ymin), mask=mask)
    
        return background, bb_list

    @classmethod
    def resizeImageFormat(cls, new_text_width, new_text_height, height, background, blur, random_blur):
        ##################################
        # Resize image to desired format #
        ##################################
        new_width = float(new_text_width + 10) * (float(height) / float(new_text_height + 10))
#         image_on_background = background.resize((int(new_text_width), height), Image.ANTIALIAS)
        image_on_background = background
        final_image = image_on_background.filter(
            ImageFilter.GaussianBlur(
                radius=(blur if not random_blur else random.randint(0, blur))
            )
        )
        
        return final_image

    @classmethod
    def generateImageName(cls, name_format, text, index, extension):
        #####################################
        # Generate name for resulting image #
        #####################################
        if name_format == 0:
            image_name = '{}_{}.{}'.format(text, str(index), extension)
        elif name_format == 1:
            image_name = '{}_{}.{}'.format(str(index), text, extension)
        elif name_format == 2:
            image_name = '{}.{}'.format(str(index),extension)
        else:
            print('{} is not a valid name format. Using default.'.format(name_format))
            image_name = '{}_{}.{}'.format(text, str(index), extension)
            
        return image_name
        
    @classmethod
    def generate(cls, index, text, font, out_dir, height, extension, skewing_angle, random_skew, blur, random_blur, background_type, distorsion_type, distorsion_orientation, is_handwritten, name_format, text_color=-1):
        image = None

        ##########################
        # Create picture of text #
        ##########################
        rotated_img_list = [ FakeTextDataGenerator.createTextPicture(is_handwritten, word, font, text_color, skewing_angle, random_skew) \
                       for word in text]

        #############################
        # Apply distorsion to image #
        #############################
        distorted_img_list = [ FakeTextDataGenerator.applyDistorsion(rotated_img, distorsion_type, distorsion_orientation) \
                         for rotated_img in rotated_img_list]
        ##TO-DO : THE NEXT LINE NEEDS CHANGE.
        new_text_width, new_text_height = distorted_img_list[0].size

        #############################
        # Generate background image #
        #############################
        background, bb_list = FakeTextDataGenerator.generateBackgroundImage(distorted_img_list, background_type)

        ##################################
        # Resize image to desired format #
        ##################################
        final_image = FakeTextDataGenerator.resizeImageFormat(new_text_width, new_text_height, height, background, blur, random_blur)

        #####################################
        # Generate name for resulting image #
        #####################################
        image_name = FakeTextDataGenerator.generateImageName(name_format, text, index, extension)

        # Save the image
        final_image.convert('RGB').save(os.path.join(out_dir, image_name))
        pickle.dump(bb_list, open(os.path.join(out_dir[:-1] + '_bb_out', image_name[:-4] + '_bb.p'), 'wb'))
