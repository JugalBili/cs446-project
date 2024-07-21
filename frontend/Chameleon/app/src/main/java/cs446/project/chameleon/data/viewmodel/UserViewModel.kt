package cs446.project.chameleon.data.viewmodel

import android.graphics.Bitmap
import android.util.Log
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.graphics.Color
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import cs446.project.chameleon.data.model.User
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import androidx.compose.runtime.*
import cs446.project.chameleon.data.model.HSL
import cs446.project.chameleon.data.model.History
import cs446.project.chameleon.data.model.HistoryData
import cs446.project.chameleon.data.model.Paint
import cs446.project.chameleon.data.model.RGB
import cs446.project.chameleon.data.repository.HistoryRepository
import cs446.project.chameleon.data.repository.ImageRepository
import cs446.project.chameleon.data.repository.UserRepository
import kotlinx.coroutines.launch

data class UIHistory (
    val baseImage: Bitmap,
    val images: List<Bitmap>,
    val colors: List<Color>
)

class UserViewModel(test: List<Bitmap>): ViewModel() {

    // Setup repo
    private var userRepository: UserRepository = UserRepository()
    private var imageRepository: ImageRepository = ImageRepository()
    private var historyRepository: HistoryRepository = HistoryRepository()

    // User object
    private var _user: User? by mutableStateOf(null)
    fun getUser(): User? {
        return _user
    }
    fun updateUser(user: User) {
        _user = user
    }

    // User token
    lateinit var token: String

    // User favourites
    private val _favourites = MutableStateFlow<List<Paint>>(emptyList())
    val favourites = _favourites.asStateFlow()
    fun addPaint(paint: Paint) {
        _favourites.value += paint
    }
    fun deleteFav(paint: Paint) {
        _favourites.value -= paint
    }

    // User history
    private val _historyList = MutableStateFlow<List<UIHistory>>(emptyList())
    val historyList = _historyList.asStateFlow()


    fun fetchUser(){
    }

    fun fetchFavourites() {
    }

    fun fetchHistory() {
        viewModelScope.launch {
            val data = historyRepository.getHistory(token)
                // TODO: Update historyList with this data
        }
    }


    // INIT TO TEST PAGE
    init {
        val defaultUser = User("asdf", "John", "Doe", "asdf")
        updateUser(defaultUser)
        val defaultPaints = listOf(
            Paint("Benjamin Moore", "https://www.benjaminmoore.com/en-ca/paint-colours/colour/2000-70/voile-pink", "Voile Pink", "2000-70", RGB(252, 226, 230), HSL(351f, 81.3f, 93.7f), "white", "red"),
            Paint("PPG", "https://www.ppgpaints.com/color/color-families/greens/grass-daisy", "Grass Daisy", "PPG1215-6", RGB(206, 176, 42), HSL(49f, 66.1f, 48.6f), "yellow", "yellow"),
            Paint("PPG", "https://www.ppgpaints.com/color/color-families/oranges/fiesta", "Fiesta", "PPG1065-2", RGB(237, 216, 210), HSL(13f, 42.9f, 87.6f), "white", "red"),
            Paint("Dunn Edwards", "https://www.dunnedwards.com/colors/browser/de5921", "Your Shadow", "DE5921", RGB(120, 126, 147), HSL(227f, 11.1f, 52.4f), "gray", "blue")
        )
        for (i in defaultPaints) {
            addPaint(i)
        }

        _historyList.value += UIHistory(test[0],test, listOf(Color.Green, Color.Yellow, Color.Blue))
        _historyList.value += UIHistory(test[0],test, listOf(Color.Green, Color.Yellow, Color.Blue))
        _historyList.value += UIHistory(test[0],test, listOf(Color.Green, Color.Yellow, Color.Blue))
        _historyList.value += UIHistory(test[0],test, listOf(Color.Green, Color.Yellow, Color.Blue))
        _historyList.value += UIHistory(test[0],test, listOf(Color.Green, Color.Yellow, Color.Blue))
        _historyList.value += UIHistory(test[0],test, listOf(Color.Green, Color.Yellow, Color.Blue))
        _historyList.value += UIHistory(test[0],test, listOf(Color.Green, Color.Yellow, Color.Blue))
    }
}