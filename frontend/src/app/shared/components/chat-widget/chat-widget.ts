import { Component, OnInit, ElementRef, ViewChild, AfterViewChecked } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ChatService, ChatMessage } from '../../../core/services/chat/chat';
import { Observable } from 'rxjs';

@Component({
  selector: 'app-chat-widget',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './chat-widget.html',
  styleUrls: ['./chat-widget.scss']
})
export class ChatWidgetComponent implements OnInit, AfterViewChecked {
  @ViewChild('scrollContainer') private scrollContainer!: ElementRef;

  isOpen = false;
  showTooltip = true;
  userInput = '';
  isTyping = false;
  
  messages$!: Observable<ChatMessage[]>;

  constructor(private chatService: ChatService) {}

  ngOnInit() {
    this.messages$ = this.chatService.messages$;
  }

  ngAfterViewChecked() {
    this.scrollToBottom();
  }

  toggleChat() {
    this.isOpen = !this.isOpen;
    if (this.isOpen) {
      this.showTooltip = false; // Al abrir, desaparece el cartel permanentemente
    }
  }

  closeTooltip(event: Event) {
    event.stopPropagation(); // Evita que se abra el chat al clickear la X
    this.showTooltip = false;
  }

  async sendMessage() {
    if (!this.userInput.trim()) return;

    const messageToSend = this.userInput;
    this.userInput = ''; // Limpiamos el input
    this.isTyping = true; // Mostramos indicador de carga

    try {
      await this.chatService.sendMessage(messageToSend);
    } finally {
      this.isTyping = false;
    }
  }

  private scrollToBottom(): void {
    try {
      this.scrollContainer.nativeElement.scrollTop = this.scrollContainer.nativeElement.scrollHeight;
    } catch(err) { }
  }
}