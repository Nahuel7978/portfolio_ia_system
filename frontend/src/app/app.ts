import { Component, signal } from '@angular/core';
import { RouterLink, RouterOutlet } from '@angular/router';
import { HeaderComponent } from "./features/header/header";
import { ChatWidgetComponent } from "./shared/components/chat-widget/chat-widget";

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, RouterLink, HeaderComponent, ChatWidgetComponent],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App {
  protected readonly title = signal('frontend-app');
}
