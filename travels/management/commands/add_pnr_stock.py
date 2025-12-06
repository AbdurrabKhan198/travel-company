"""
Management command to add PNRs to stock (Route-specific)
Usage: 
  python manage.py add_pnr_stock --route <route_id> --generate 100
  python manage.py add_pnr_stock --route <route_id> PNR1 PNR2 PNR3
  python manage.py add_pnr_stock --route <route_id> --file pnr_list.txt
  python manage.py add_pnr_stock --all-routes --generate 50 (adds to all routes)
"""

from django.core.management.base import BaseCommand
from travels.models import PNRStock, Route
import random
import string


class Command(BaseCommand):
    help = 'Add PNRs to stock for specific routes. PNRs are route-specific and can only be assigned to passengers booking that route.'

    def add_arguments(self, parser):
        parser.add_argument(
            'pnrs',
            nargs='*',
            type=str,
            help='Individual PNR codes to add'
        )
        parser.add_argument(
            '--route',
            type=int,
            help='Route ID to add PNRs for (required unless using --all-routes)'
        )
        parser.add_argument(
            '--all-routes',
            action='store_true',
            help='Add PNRs to all routes (use with --generate)'
        )
        parser.add_argument(
            '--file',
            type=str,
            help='Path to file containing PNRs (one per line)'
        )
        parser.add_argument(
            '--generate',
            type=int,
            help='Generate N random PNRs and add to stock'
        )
        parser.add_argument(
            '--format',
            type=str,
            default='alphanumeric',
            choices=['alphanumeric', 'numeric', 'alpha'],
            help='Format for generated PNRs (default: alphanumeric)'
        )
        parser.add_argument(
            '--length',
            type=int,
            default=6,
            help='Length of generated PNRs (default: 6)'
        )

    def handle(self, *args, **options):
        # Get routes to add PNRs for
        routes = []
        if options['all_routes']:
            routes = list(Route.objects.all())
            if not routes:
                self.stdout.write(self.style.ERROR('No routes found in database. Please create routes first.'))
                return
            self.stdout.write(self.style.SUCCESS(f'Found {len(routes)} route(s)'))
        elif options['route']:
            try:
                route = Route.objects.get(id=options['route'])
                routes = [route]
            except Route.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Route with ID {options["route"]} not found.'))
                return
        else:
            self.stdout.write(self.style.ERROR('Either --route <route_id> or --all-routes is required.'))
            self.stdout.write(self.style.WARNING('Use --help for usage information.'))
            return
        
        pnrs_to_add = []
        
        # Add individual PNRs from command line
        if options['pnrs']:
            pnrs_to_add.extend(options['pnrs'])
        
        # Add PNRs from file
        if options['file']:
            try:
                with open(options['file'], 'r') as f:
                    file_pnrs = [line.strip() for line in f if line.strip()]
                    pnrs_to_add.extend(file_pnrs)
                    self.stdout.write(self.style.SUCCESS(f'Read {len(file_pnrs)} PNRs from file'))
            except FileNotFoundError:
                self.stdout.write(self.style.ERROR(f'File not found: {options["file"]}'))
                return
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error reading file: {str(e)}'))
                return
        
        # Generate random PNRs
        if options['generate']:
            count = options['generate']
            length = options['length']
            format_type = options['format']
            
            for _ in range(count):
                if format_type == 'numeric':
                    pnr = ''.join(random.choices(string.digits, k=length))
                elif format_type == 'alpha':
                    pnr = ''.join(random.choices(string.ascii_uppercase, k=length))
                else:  # alphanumeric
                    pnr = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
                pnrs_to_add.append(pnr)
            
            self.stdout.write(self.style.SUCCESS(f'Generated {count} random PNRs'))
        
        if not pnrs_to_add:
            self.stdout.write(self.style.WARNING('No PNRs to add. Use --help for usage information.'))
            return
        
        # Add PNRs to stock for each route
        total_added = 0
        total_skipped = 0
        all_errors = []
        
        for route in routes:
            self.stdout.write(self.style.SUCCESS(f'\n📋 Processing Route: {route.from_location} → {route.to_location} ({route.carrier_number})'))
            
            added_count = 0
            skipped_count = 0
            errors = []
            
            for pnr in pnrs_to_add:
                pnr = pnr.strip().upper()
                if not pnr:
                    continue
                
                # Check if PNR already exists for this route
                if PNRStock.objects.filter(pnr=pnr, route=route).exists():
                    skipped_count += 1
                    errors.append(f'PNR {pnr} already exists for this route')
                    continue
                
                try:
                    PNRStock.objects.create(pnr=pnr, route=route, is_assigned=False)
                    added_count += 1
                except Exception as e:
                    skipped_count += 1
                    errors.append(f'Error adding PNR {pnr}: {str(e)}')
            
            total_added += added_count
            total_skipped += skipped_count
            all_errors.extend(errors)
            
            self.stdout.write(self.style.SUCCESS(f'  ✓ Added {added_count} PNR(s) for this route'))
            if skipped_count > 0:
                self.stdout.write(self.style.WARNING(f'  ⚠ Skipped {skipped_count} PNR(s)'))
        
        # Summary
        self.stdout.write(self.style.SUCCESS(f'\n✅ Overall Summary:'))
        self.stdout.write(self.style.SUCCESS(f'  ✓ Successfully added {total_added} PNR(s) across {len(routes)} route(s)'))
        if total_skipped > 0:
            self.stdout.write(self.style.WARNING(f'  ⚠ Skipped {total_skipped} PNR(s)'))
            if all_errors:
                for error in all_errors[:10]:  # Show first 10 errors
                    self.stdout.write(self.style.ERROR(f'  - {error}'))
                if len(all_errors) > 10:
                    self.stdout.write(self.style.ERROR(f'  ... and {len(all_errors) - 10} more errors'))
        
        # Show current stock status by route
        self.stdout.write(self.style.SUCCESS(f'\n📊 Current PNR Stock Status by Route:'))
        for route in routes:
            route_pnrs = PNRStock.objects.filter(route=route)
            total = route_pnrs.count()
            available = route_pnrs.filter(is_assigned=False).count()
            assigned = route_pnrs.filter(is_assigned=True).count()
            self.stdout.write(f'  {route.from_location} → {route.to_location}: Total={total}, Available={available}, Assigned={assigned}')
        
        # Overall summary
        total_pnrs = PNRStock.objects.count()
        available_pnrs = PNRStock.objects.filter(is_assigned=False).count()
        assigned_pnrs = PNRStock.objects.filter(is_assigned=True).count()
        
        self.stdout.write(self.style.SUCCESS(f'\n📊 Overall PNR Stock Status:'))
        self.stdout.write(f'  Total PNRs: {total_pnrs}')
        self.stdout.write(f'  Available: {available_pnrs}')
        self.stdout.write(f'  Assigned: {assigned_pnrs}')

