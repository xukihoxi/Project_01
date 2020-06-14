# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from os import path
import logging

logger = logging.getLogger(__name__)


class GetFileStorage(http.Controller):
    @http.route(["/data/filestore_dir/partner_files/<string:filepath>/<string:filename>"], auth='user')
    def GetFileStorage(self, filepath, filename):
        try:
            file_path = '%s/%s/%s' % (
                '/data/filestore_dir/partner_files',
                filepath,
                filename
            )
            filecontent = open(file_path, 'rb').read()
            # logger.error("New path mapped!")
        except:
            source_path = path.dirname(__file__)
            index_path = source_path.find('addons_custom')
            if source_path[index_path - 1] != '\\' and source_path[index_path - 1] != '/':
                file_path = source_path[:index_path] + '/../filestore_dir/partner_files/' + filepath + '/' + filename
            else:
                file_path = source_path[:index_path] + '../filestore_dir/partner_files/' + filepath + '/' + filename
            filecontent = open(file_path, 'rb').read()
            # logger.error("Old path mapped!")
        extension_type = filename.lower()
        if extension_type.endswith('.pdf'):
            content_type = 'application/pdf'
        elif extension_type.endswith('.png') or extension_type.endswith('.jpg') or extension_type.endswith(
                '.jpeg') or extension_type.endswith('.gif'):
            content_type = 'image/jpeg'
        elif extension_type.endswith('.mp4'):
            content_type = 'video/mp4'
        elif extension_type.endswith('.3gp'):
            content_type = 'video/3gpp'
        elif extension_type.endswith('avi'):
            content_type = 'video/x-msvideo'
        else:
            content_type = 'application/octet-stream'
        return request.make_response(filecontent,
                                     [('Content-Type', content_type),
                                      ('Content-Length', len(filecontent)),
                                      ('Content-Disposition', ':attachment; filename=%s' % filename)])
