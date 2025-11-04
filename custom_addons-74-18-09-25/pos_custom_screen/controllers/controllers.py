# -*- coding: utf-8 -*-
# from odoo import http


# class PosCustomScreen(http.Controller):
#     @http.route('/pos_custom_screen/pos_custom_screen', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pos_custom_screen/pos_custom_screen/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('pos_custom_screen.listing', {
#             'root': '/pos_custom_screen/pos_custom_screen',
#             'objects': http.request.env['pos_custom_screen.pos_custom_screen'].search([]),
#         })

#     @http.route('/pos_custom_screen/pos_custom_screen/objects/<model("pos_custom_screen.pos_custom_screen"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pos_custom_screen.object', {
#             'object': obj
#         })

