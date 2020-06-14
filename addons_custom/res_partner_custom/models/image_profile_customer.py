# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import except_orm, ValidationError
from odoo import sys, os
import base64, time
from os.path import  join


# sys.setdefaultencoding('utf-8')
# Create Folder
source_folder_path = os.path.dirname(__file__)
index_folder_path = source_folder_path.find('addons_custom')
if source_folder_path[index_folder_path - 1] != '\\' and source_folder_path[index_folder_path - 1] != '/':
    folder_path = source_folder_path[:index_folder_path] + '/filestore_dir/partner_files'
else:
    folder_path = source_folder_path[:index_folder_path] + 'filestore_dir/partner_files'
if not os.path.exists(folder_path):
    os.mkdir(folder_path)
folder_path = folder_path + '/'
NUMBER_SEQUENCE = 1


class Image(models.Model):
    _name = "izi.images.profile.customer"

    name = fields.Char()
    image = fields.Binary('Image', attachment=True)
    # image_name= fields.Char('Image Name')
    partner_id = fields.Many2one('res.partner', "Partner")
    path = fields.Char(string='Path')

    # @api.onchange('image')
    # def onchange_image(self):
    #     if self.image:
    #         # name, extension = self.get_file_extension(self.name)
    #         # self.name = name + '(' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S') + ')' + extension
    #         try:
    #
    #             os.mkdir(folder_path + str(self.partner_id.x_code))
    #         except FileExistsError:
    #             pass
    #         except Exception as e:
    #             pass
    #         image_full_path = join( folder_path, str(self.partner_id.x_code), str(str(datetime.now().date()) + '_' + str(time.time())) )
    #         f = open( image_full_path , 'wb')
    #         f.write(base64.b64decode(self.image))
    #         f.close()
    #         # print("file name", image_full_path)
    #         os.rename(image_full_path, image_full_path+'.png')
    #
    @api.model
    def create(self, vals):
        res = super(Image, self).create(vals)
        if res.image:
            # name, extension = self.get_file_extension(self.name)
            # self.name = name + '(' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S') + ')' + extension
            try:

                os.mkdir(folder_path + str(res.partner_id.x_code))
            except FileExistsError:
                pass
            except Exception as e:
                pass
            image_full_path = join( folder_path, str(res.partner_id.x_code), str(str(datetime.now().date()) + '_' + str(time.time())) )
            f = open( image_full_path , 'wb')
            f.write(base64.b64decode(res.image))
            f.close()
            # print("file name", image_full_path)
            os.rename(image_full_path, image_full_path+'.png')
        return res
    # @api.multi
    # def create(self):
    #     super(Image,self).create()
    #


    def get_file_extension(self, path):
        filename, file_extension = os.path.splitext(path)
        return filename, file_extension

