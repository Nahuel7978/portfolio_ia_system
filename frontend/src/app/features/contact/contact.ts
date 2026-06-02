import { Component, inject, afterNextRender, ElementRef } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { ContactService } from '../../core/services/contact';
import { HttpErrorResponse } from '@angular/common/http';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-contact',
  standalone: true,
  imports: [ReactiveFormsModule, CommonModule],
  templateUrl: './contact.html'
})
export class ContactComponent {
  private fb = inject(FormBuilder);
  private contactService = inject(ContactService);
  private el = inject(ElementRef);

  contactForm: FormGroup = this.fb.nonNullable.group({
    name: ['', Validators.required],
    email: ['', [Validators.required, Validators.email]],
    subject: ['', Validators.required],
    message: ['', Validators.required]
  });

  isLoading = false;
  isSuccess = false;
  errorMessage = '';

  constructor() {
    // API exclusiva del navegador - Seguro para SSR
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

  onSubmit() {
    if (this.contactForm.invalid) {
      this.contactForm.markAllAsTouched();
      return;
    }

    this.isLoading = true;
    this.isSuccess = false;
    this.errorMessage = '';

    this.contactService.sendMessage(this.contactForm.getRawValue()).subscribe({
      next: () => {
        this.isLoading = false;
        this.isSuccess = true;
        this.contactForm.reset();
        setTimeout(() => this.isSuccess = false, 5000);
      },
      error: (err: HttpErrorResponse) => {
        this.isLoading = false;
        if (err.status === 429) {
          this.errorMessage = 'Has enviado demasiados mensajes. Por favor, intenta más tarde.';
        } else {
          this.errorMessage = 'Ocurrió un error de conexión. Inténtalo de nuevo.';
        }
      }
    });
  }
}