import { Component, afterNextRender, ElementRef, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ContactComponent } from '../contact/contact';
import { ProjectsComponent } from '../projects/projects';
import { BlogsComponent } from '../blogs/blogs';
import { AboutComponent } from "../about/about";

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, ContactComponent, ProjectsComponent, BlogsComponent, AboutComponent],
  templateUrl: './home.html'
})
export class HomeComponent {
  private el = inject(ElementRef);

  constructor() {
    afterNextRender(() => {
      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible');
          }
        });
      }, { threshold: 0.15 });

      this.el.nativeElement.querySelectorAll('.section-reveal').forEach((el: Element) => observer.observe(el));
    });
  }
}