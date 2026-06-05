import { Component, OnInit, inject, PLATFORM_ID, ChangeDetectorRef, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule, isPlatformBrowser } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { LucideAngularModule, CheckCircle2 } from 'lucide-angular';

@Component({
  selector: 'app-about',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  templateUrl: './about.html',
  // SOLUCIÓN ARQUITECTÓNICA: Cortamos la detección de cambios automática
  changeDetection: ChangeDetectionStrategy.OnPush 
})
export class AboutComponent implements OnInit {
  private http = inject(HttpClient);
  private platformId = inject(PLATFORM_ID);
  private cdr = inject(ChangeDetectorRef);

  aboutText = '';
  technologies: string[] = [];

  readonly CheckCircle2 = CheckCircle2;

  ngOnInit() {
    if (isPlatformBrowser(this.platformId)) {
      
      // Petición 1: Texto
      this.http.get('/content/about.txt', { responseType: 'text' }).subscribe({
        next: (text) => {
          this.aboutText = text;
          // Le avisamos a Angular que esta variable ya está lista para pintarse
          this.cdr.markForCheck(); 
        },
        error: (err) => console.error('Error cargando about.txt', err)
      });

      // Petición 2: Tecnologías
      this.http.get('/content/tech.txt', { responseType: 'text' }).subscribe({
        next: (text) => {
          this.technologies = text.split('\n')
                                  .map(t => t.trim())
                                  .filter(t => t.length > 0);
          // Le avisamos a Angular que la lista ya está lista para pintarse
          this.cdr.markForCheck();
        },
        error: (err) => console.error('Error cargando tech.txt', err)
      });
      
      setTimeout(() => this.initScrollAnimation(), 100);
    } else {
       this.aboutText = 'Software Engineer & Systems Architect.';
    }
  }

  private initScrollAnimation() {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1 });
    
    document.querySelectorAll('.section-reveal').forEach(el => observer.observe(el));
  }
}