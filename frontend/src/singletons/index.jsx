import { store } from '../storage/store';
import uploadTrackingService from './uploadTrackingService';

uploadTrackingService.setStore(store);

export {
  uploadTrackingService,
}