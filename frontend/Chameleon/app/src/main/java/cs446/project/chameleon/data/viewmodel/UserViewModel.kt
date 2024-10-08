package cs446.project.chameleon.data.viewmodel

import android.graphics.Bitmap
import androidx.compose.runtime.mutableStateOf
import cs446.project.chameleon.data.model.Color
import androidx.lifecycle.ViewModel
import cs446.project.chameleon.data.model.User
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import androidx.compose.runtime.*
import cs446.project.chameleon.data.model.Favorite
import cs446.project.chameleon.data.model.HSL
import cs446.project.chameleon.data.model.History
import cs446.project.chameleon.data.model.LoginResponse
import cs446.project.chameleon.data.model.Paint
import cs446.project.chameleon.data.model.RGB
import cs446.project.chameleon.data.model.Review
import cs446.project.chameleon.data.model.Token
import cs446.project.chameleon.data.repository.FavoriteRepository
import cs446.project.chameleon.data.repository.GalleryRepository
import cs446.project.chameleon.data.repository.HistoryRepository
import cs446.project.chameleon.data.repository.ImageRepository
import cs446.project.chameleon.data.repository.UserRepository
import cs446.project.chameleon.utils.getPaintById
import kotlinx.coroutines.GlobalScope
import kotlinx.coroutines.async
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.runBlocking
import okhttp3.internal.wait

data class UIHistory (
    var baseImageId: String,
    var baseImage: Bitmap,
    val imageIds: List<String>,
    val colors: List<Color>
)

class UserViewModel(test: List<Bitmap>): ViewModel() {

    // Setup repo
    private var userRepository: UserRepository = UserRepository()
    private var imageRepository: ImageRepository = ImageRepository()
    private var favoriteRepository: FavoriteRepository = FavoriteRepository()
    private var historyRepository: HistoryRepository = HistoryRepository()
    private var galleryRepository: GalleryRepository = GalleryRepository()

    // User object
    private var _user: User? by mutableStateOf(null)
    fun getUser(): User? {
        return _user
    }
    fun updateUser(user: User) {
        _user = user
    }

    // User token
    lateinit var token: Token

    private val _favourites = MutableStateFlow<List<Paint>>(emptyList())
    val favourites = _favourites.asStateFlow()
    fun getFavourites(): List<Paint> {
        return _favourites.value
    }
    fun addPaint(paint: Paint) {
        _favourites.value += paint
    }
    fun deletePaint(paint: Paint) {
        _favourites.value -= paint
    }

    // User history
    private val _historyList = MutableStateFlow<List<UIHistory>>(emptyList())
    val historyList = _historyList.asStateFlow()
    fun addHistory(history: UIHistory) {
        _historyList.value += history
    }
    fun deleteHistory(history: UIHistory) {
        _historyList.value -= history
    }


    suspend fun loginUser(email: String, password: String): String? {
        try {
            val response = userRepository.login(email, password)

            token = response.token
            _user = response.user

            runBlocking {
                fetchFavourites()
            }

            runBlocking {
                fetchHistory()
            }

            return null
        } catch (e: Exception) {
            return "Login unsuccessful"
        }
    }

    suspend fun registerUser(email: String, password: String, firstname: String, lastname: String): String? {
        try {
            runBlocking {
                userRepository.register(email, password, firstname, lastname)
                loginUser(email, password)
            }
            return null
        } catch (e: Exception) {
            return "Register unsuccessful"
        }
    }

    // favourites
    suspend fun fetchFavourites() {
        _favourites.value = emptyList()
        val response = favoriteRepository.getFavorites(token.token)
        for (fav in response) {
            addPaint(getPaintById(fav.paintId))
        }
    }

    suspend fun addFavourite(paint: Paint) {
        val fav = Favorite(paint.id, paint.rgb)
        favoriteRepository.postFavorite(token.token, fav)

        runBlocking {
            fetchFavourites()
        }
    }

    suspend fun deleteFavourite(paint: Paint) {
        favoriteRepository.deleteFavorite(token.token, paint.id)

        runBlocking {
            fetchFavourites()
        }
    }

    // history
    suspend fun fetchHistory() {
        _historyList.value = emptyList()

        val response = historyRepository.getHistory(token.token)

        for (history in response.history) {
            val imgRes = imageRepository.getImageList(token.token, history.baseImage)

            // get original image
            val baseImage = imageRepository.getImageBitmap(token.token, imgRes.originalImage)

            // get renders
            val imageIds = mutableListOf<String>()
            for (img in imgRes.processedImages) {
                imageIds.add(img.processedImageHash)
            }

            addHistory(UIHistory(imgRes.originalImage, baseImage, imageIds, history.colors))

            // TODO FIX
            //break
        }
    }

    // fetched non-cached rendered images for a base image
    suspend fun fetchNonCachedHistory(): String? {
        try {
            val response = historyRepository.getHistory(token.token)

            for (history in response.history) {
                if (!historyList.value.any { it.baseImageId == history.baseImage }) {
                    val baseImage = imageRepository.getImageBitmap(token.token, history.baseImage)
                    val imgRes = imageRepository.getImageList(token.token, history.baseImage)

                    val imageIds = mutableListOf<String>()
                    for (img in imgRes.processedImages) {
                        imageIds.add(img.processedImageHash)
                    }

                    addHistory(UIHistory(imgRes.originalImage, baseImage, imageIds, history.colors))
                }
            }

            return null
        } catch (e: Exception) {
            return "Connection to server failed"
        }
    }

    // fetch rendered images for a base image
    suspend fun fetchRenderedFromHistory(imageIds: List<String>): List<Bitmap> {
        val images = mutableListOf<Bitmap>()

        for (imgHash in imageIds) {
            images.add(imageRepository.getImageBitmap(token.token, imgHash))
        }

        return images
    }

    // Review calls
    private val _reviews = MutableStateFlow<List<Review>>(emptyList())
    val reviews = _reviews.asStateFlow()
    fun getReviews(): List<Review> {
        return _reviews.value
    }
    suspend fun fetchReviews(paintId: String) {
        _reviews.value = galleryRepository.getAllReviews(token.token, paintId)
    }
    suspend fun createReview(paintId: String, review: String) {
        runBlocking {
            galleryRepository.createImagelessReview(token.token, paintId, review)
        }
    }
}
