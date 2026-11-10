export type ToastTone = 'success' | 'error' | 'info';

export type ToastItem = {
	id: number;
	message: string;
	tone: ToastTone;
};

class ToastStore {
	items = $state<ToastItem[]>([]);
	private nextId = 1;

	show(message: string, tone: ToastTone = 'success') {
		const id = this.nextId++;
		this.items = [...this.items, { id, message, tone }];
		setTimeout(() => this.dismiss(id), 2600);
	}

	dismiss(id: number) {
		this.items = this.items.filter((item) => item.id !== id);
	}
}

export const toast = new ToastStore();
