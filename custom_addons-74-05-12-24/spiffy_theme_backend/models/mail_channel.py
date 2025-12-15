# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
# Developed by Bizople Solutions Pvt. Ltd.

from odoo import models
import requests

class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'
    

    def _notify_thread(self, message, msg_vals=False, **kwargs):
        rdata = super(MailThread, self)._notify_thread(message, msg_vals=msg_vals, **kwargs)
        self._notify_record_firebase(message, rdata, msg_vals, **kwargs)
        return rdata
    
    def _notify_record_firebase(self, message, rdata, msg_vals=False, **kwargs):
        """ We want to send a Cloud notification for every mentions of a partner
        and every direct message. We have to take into account the risk of
        duplicated notifications in case of a mention in a channel of `chat` type.
        """
        
        notif_pids = [r['id'] for r in rdata if r['active']]
        no_inbox_pids = [r['id'] for r in rdata if r['active'] and r['notif'] != 'inbox']
        if not notif_pids:
            return

        msg_vals = dict(msg_vals or {})
        msg_sudo = message.sudo()
        msg_type = msg_vals.get('message_type') or msg_sudo.message_type
        author_id = [msg_vals.get('author_id')] if 'author_id' in msg_vals else msg_sudo.author_id.ids
        if msg_type == 'comment':
            pids = set(notif_pids) - set(author_id)
            for id in pids:
                user_obj = self.env['res.users'].search([('partner_id','=',int(id))])     
                device_ids = user_obj.mail_firebase_tokens.mapped('token') if user_obj else False
                self._prepare_firebase_notifications(message,device_ids)
        elif msg_type in ('notification', 'user_notification', 'email'):
            pids = (set(notif_pids) - set(author_id) - set(no_inbox_pids))
            for id in pids:
                user_obj = self.env['res.users'].search([('partner_id','=',int(id))])     
                device_ids = user_obj.mail_firebase_tokens.mapped('token') if user_obj else False
                self._prepare_firebase_notifications(message,device_ids)
        

    def _prepare_firebase_notifications(self, message, device_ids):
        message_json = {
            'author_id': message['author_id'],
            'body': message['body'][3:-4],
            'body_html': message['body'],
            'res_id':message['res_id'],
            'model':message['model']
        }
        
        self._mail_channel_firebase_notifications(message_json, device_ids)

    def _mail_channel_firebase_notifications(self, message, device_ids):
        """
            Send notifications via Firebase Cloud
        """
        if not device_ids:
            return
        key = self.env.company.firebase_server_key
        if not key:
            return
        url = 'https://fcm.googleapis.com/fcm/send'

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'key={}'.format(key)
        }
        
        action = self.env.ref('mail.action_discuss')
        menu = self.env.ref('mail.menu_root_discuss')
        if message['model'] == 'mail.channel':
            channel_url = f'/web?bg_color=True&tool_color_id=1#menu_id={str(menu.id)}&default_active_id=mail.box_inbox&action={str(action.id)}&active_id=mail.channel_{str(message["res_id"])}'
        else:
            channel_url = f'/web?bg_color=True&tool_color_id=1#default_active_id=mail.box_inbox&action={str(action.id)}&menu_id={str(menu.id)}&active_id=mail.box_inbox'
        if len(device_ids) > 1:
            data = {
                "notification": {
                    'title': message['author_id'].name,
                    'body': message['body'],
                    'sound': "default",
                    'badge': None,
                },
                'dry_run': False,
                'priority': 'high',
                'content_available': True,
                "data": {
                    "body_html": message['body_html'],
                    'res_id':message['res_id'],
                    'click_action':channel_url,

                },
                "registration_ids": device_ids,
            }
        else:
            data = {
                "notification": {
                    'title': message['author_id'].name,
                    'body': message['body'],
                    'res_id':message['res_id'],
                    'sound': "default",
                    'badge': None,
                },
                'dry_run': False,
                'priority': 'high',
                'content_available': True,
                "data": {
                    "body_html": message['body_html'],
                    'click_action':channel_url,
                },
                "to": ''.join(device_ids),
            }
        resonse_data = requests.post(url, json=data, headers=headers)
        
        


class Channel(models.Model):
    _inherit = 'mail.channel'


    def _notify_record_firebase(self, message, rdata, msg_vals=False, **kwargs):
        """ Specifically handle channel members. """
        chat_channels = self.filtered(lambda channel: channel.channel_type == 'chat')
        channel_channels = self.filtered(lambda channel: channel.channel_type == 'channel')
        if chat_channels:
            # modify rdata only for calling super. Do not deep copy as we only
            # add data into list but we do not modify item content
            channel_rdata = rdata.copy()
            channel_rdata += [
                {'id': partner.id,
                 'share': partner.partner_share,
                 'active': partner.active,
                 'notif': 'ocn',
                 'type': 'customer',
                 'groups': [],
                }
                for partner in chat_channels.mapped("channel_partner_ids")
            ]
        elif channel_channels:
            channel_rdata = rdata.copy()
            channel_rdata += [
                {'id': partner.id,
                 'share': partner.partner_share,
                 'active': partner.active,
                 'notif': 'ocn',
                 'type': 'customer',
                 'groups': [],
                }
                for partner in channel_channels.mapped("channel_partner_ids")
            ]
        else:
            channel_rdata = rdata
        return super(Channel, self)._notify_record_firebase(message, channel_rdata, msg_vals=msg_vals, **kwargs)