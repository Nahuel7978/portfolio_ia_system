import { afterNextRender, Component, ElementRef, inject } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { AuthService } from '../../../core/services/auth.service';
import { CommonModule } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Router } from '@angular/router';

@Component({
  selector: 'app-login',
  imports: [ReactiveFormsModule, CommonModule],
  templateUrl: './login.html',
  styleUrl: './login.scss',
})
export class LoginComponent {
  private fb = inject(FormBuilder);
  private authService = inject(AuthService);
  private el = inject(ElementRef);
  private router = inject(Router);

  loginForm: FormGroup = this.fb.nonNullable.group({
    username: ['', Validators.required],
    password: ['', [Validators.required]]
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
    if (this.loginForm.invalid) {
      this.loginForm.markAllAsTouched();
      return;
    }

    this.isLoading = true;
    this.isSuccess = false;
    this.errorMessage = '';

    this.authService.login(this.loginForm.getRawValue()).subscribe({
      next: () => {
        this.isLoading = false;
        this.isSuccess = true;
        this.router.navigate(['/admin/technologies']);
      },
      error: (err: HttpErrorResponse) => {
        this.isLoading = false;
        if (err.status === 401) {
          this.errorMessage = 'Usuario o Contraseña incorrectos. Inténtalo de nuevo.';
        } else {
          this.errorMessage = 'Ocurrió un error de conexión. Inténtalo de nuevo.';
        }
      }
    });
  }

}
