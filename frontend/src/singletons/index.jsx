import { store } from '../services/storage/store';
import uploadTrackingService from '../features/uploadTracking/uploadTrackingService';

uploadTrackingService.setStore(store);

export {
  uploadTrackingService,
}