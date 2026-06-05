import { Component, OnInit, inject } from '@angular/core';
import { AuthService } from '../../core/services/auth.service';
import { RouterLink } from "@angular/router";


@Component({
  selector: 'app-header',
  standalone: true,
  imports: [RouterLink],
  templateUrl: './header.html',
})
export class HeaderComponent implements OnInit {
  login: boolean = false;
  private authService = inject(AuthService);

  ngOnInit() {
    // Suscribirse al estado de autenticación en tiempo real
    this.authService.authStatus$.subscribe(status => {
      this.login = status;
    });
  }

  // Puedes usar este método si el Header incluye el botón de "Cerrar Sesión"
  onLogout() {
    this.authService.logout();

  }
}