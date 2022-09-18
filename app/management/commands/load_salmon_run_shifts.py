import argparse

import httpx
from django.conf import settings
from django.core.management.base import BaseCommand

import splatnet3
from app import services


class Command(BaseCommand):
    help = "Load Salmon Run shifts from Splatnet 3"

    def add_arguments(self, parser: argparse.ArgumentParser):
        parser.add_argument('--proxy', help='Proxy URL')
        parser.add_argument('--ca-cert', help='Path to proxy CA cert')

    def handle(self, proxy, ca_cert, **kwargs):
        session_token = settings.NINTENDO_SESSION_TOKEN
        if proxy:
            proxies = {'all://': proxy}
            client = httpx.Client(proxies=proxies, verify=ca_cert)
        else:
            client = httpx.Client()
        with client:
            bullet_token = splatnet3.get_bullet_token_from_session_token(
                client, session_token
            )
            schedule = splatnet3.get_schedule(client, bullet_token)

        shifts = services.load_salmon_run_shifts(schedule)
        self.stdout.write(self.style.SUCCESS(f"Loaded {len(shifts)} shifts:"))
        for shift in shifts:
            self.stdout.write(str(shift))
