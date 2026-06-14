import { Component, ElementRef, ViewChild, inject, OnInit, PLATFORM_ID, NgZone, ChangeDetectorRef } from '@angular/core'; // <-- Importar ChangeDetectorRef
import { CommonModule, isPlatformBrowser } from '@angular/common';
import { RouterLink } from '@angular/router';
import { KnowledgeEntryService } from '../../core/services/knowledge-entry';
import { KnowledgeEntryDTO } from '../../core/models/knowledge-entry.interface';
import { environment } from '../../../environments/environment.development';
import { LucideAngularModule, ChevronLeft, ChevronRight, Code2 } from 'lucide-angular';

@Component({
  selector: 'app-projects',
  standalone: true,
  imports: [CommonModule, RouterLink, LucideAngularModule],
  templateUrl: './projects.html'
})
export class ProjectsComponent implements OnInit {
  private entryService = inject(KnowledgeEntryService);
  private platformId = inject(PLATFORM_ID);
  private zone = inject(NgZone);
  
  // EL CAPATAZ
  private cdr = inject(ChangeDetectorRef);

  projects: KnowledgeEntryDTO[] = [];
  apiUrl = environment.apiUrl;
  isVisible = false;

  readonly ChevronLeft = ChevronLeft;
  readonly ChevronRight = ChevronRight;
  readonly Code2 = Code2;

  @ViewChild('carouselContainer') carousel!: ElementRef;
  @ViewChild('sectionTarget') sectionTarget!: ElementRef;

  ngOnInit() {
    this.entryService.getProjects().subscribe(data => {
      this.projects = data.sort((a, b) => Number(b.id) - Number(a.id));
      
      if (isPlatformBrowser(this.platformId)) {
        setTimeout(() => this.initScrollAnimation(), 50);
      } else {
        this.isVisible = true;
      }
      
      // Forzar redibujado de las tarjetas en el carrusel
      this.cdr.detectChanges(); 
    });
  }

  scroll(direction: number) {
    if (this.carousel) {
      this.carousel.nativeElement.scrollBy({ left: direction * 320, behavior: 'smooth' });
    }
  }

  private initScrollAnimation() {
    if (!this.sectionTarget) {
      this.isVisible = true;
      this.cdr.detectChanges();
      return;
    }

    // Validación SPA Inmediata para el botón "Back"
    const rect = this.sectionTarget.nativeElement.getBoundingClientRect();
    if (rect.top < window.innerHeight && rect.bottom > 0) {
      this.zone.run(() => {
        this.isVisible = true;
        this.cdr.detectChanges(); // Despertar y redibujar animación
      });
      return; // Si ya estaba visible, no creamos el observador
    }

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          this.zone.run(() => {
            this.isVisible = true;
            this.cdr.detectChanges(); // Despertar y redibujar animación
          });
          observer.disconnect(); 
        }
      });
    }, { threshold: 0.1 });

    observer.observe(this.sectionTarget.nativeElement);
  }
}
