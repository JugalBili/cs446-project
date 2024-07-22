package cs446.project.chameleon.data.viewmodel

import android.graphics.Bitmap
import android.util.Log
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import cs446.project.chameleon.data.model.Color
import cs446.project.chameleon.data.model.Paint
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow

class ImageViewModel(): ViewModel() {
    // Base image
    private val _baseImage = MutableLiveData<Bitmap>()
    val baseImage: LiveData<Bitmap> get() = _baseImage

    fun updateImage(newBitmap: Bitmap) {
        _baseImage.value = newBitmap
    }

    // Renders
    private val _renders = MutableStateFlow<List<Bitmap>>(emptyList())
    val renders = _renders.asStateFlow()

    fun updateRenders(newRenders: List<Bitmap>) {
        _renders.value = newRenders
    }

    // Corresponding Colors for Renders
    private val _renderColors = MutableStateFlow<List<Color>>(emptyList())
    val renderColors = _renderColors.asStateFlow()

    fun updateRenderColors(newColors: List<Color>) {
        _renderColors.value = newColors
    }

    fun onHistoryRowClick(uiHistory: UIHistory) {
        updateImage(uiHistory.baseImage)
        updateRenders(uiHistory.images)
        updateRenderColors(uiHistory.colors)
    }

    fun postImage(authToken: String, paints: List<Paint>) {
        // TODO: Use baseimage to update renders and renderColors
    }
}
