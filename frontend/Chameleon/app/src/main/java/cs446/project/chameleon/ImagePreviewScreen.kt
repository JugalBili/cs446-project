package cs446.project.chameleon

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.KeyboardArrowUp
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.navigation.NavHostController
import kotlinx.coroutines.launch
import kotlinx.coroutines.delay

@Composable
fun ImagePreviewScreen(navController: NavHostController) {
    val capturedImage = navController.previousBackStackEntry?.savedStateHandle?.get<Bitmap>("capturedImage")
    var isProcessing by remember { mutableStateOf(false) }
    val coroutineScope = rememberCoroutineScope()

    // FOR DEMO PURPOSES, final processed image TODO remove after
    val demoBitmap = BitmapFactory.decodeResource(LocalContext.current.resources, R.drawable.demo_after)

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color.Black)
    ) {
        capturedImage?.let { image ->
            Image(
                bitmap = image.asImageBitmap(),
                contentDescription = "Captured Photo",
                modifier = Modifier
                    .fillMaxSize(),
                contentScale = ContentScale.Crop
            )
        }

        // Retake Button
        IconButton(
            onClick = { navController.popBackStack() },
            modifier = Modifier
                .align(Alignment.TopStart)
                .padding(32.dp)
        ) {
            Icon(
                imageVector = Icons.AutoMirrored.Filled.ArrowBack,
                contentDescription = "Retake Photo",
                tint = Color.White
            )
        }

        Row(
            modifier = Modifier
                .fillMaxWidth()
                .align(Alignment.BottomCenter)
                .background(Color.Black.copy(alpha = 0.5f))
                .padding(16.dp),
            horizontalArrangement = Arrangement.SpaceAround
        ) {
            IconButton(onClick = {

            }) {
                Icon(
                    imageVector = Icons.Default.Home,
                    contentDescription = "Empty button for now",
                    tint = Color.White
                )
            }
            IconButton(onClick = {

            }) {
                Icon(
                    imageVector = Icons.Default.KeyboardArrowUp,
                    contentDescription = "Color Picker",
                    tint = Color.White
                )
            }
            IconButton(onClick = {
                // process the image, then display result
                isProcessing = true
                coroutineScope.launch {
                    processImage(demoBitmap) { processedImage-> // TODO change demoBitmap to actual result
                        navController.currentBackStackEntry?.savedStateHandle?.set("processedImage", processedImage)
                        isProcessing = false
                        navController.navigate("image_result_screen")
                    }
                }
            }) {
                Icon(
                    imageVector = Icons.Default.Check,
                    contentDescription = "Generate Image",
                    tint = Color.White
                )
            }
        }

        if (isProcessing) {
            CircularProgressIndicator(
                modifier = Modifier
                    .align(Alignment.Center)
            )
        }
    }
}

// TODO implement
suspend fun processImage(bitmap: Bitmap?, onProcessingComplete: (Bitmap) -> Unit) {
    if (bitmap == null) return
    // make backend call here; for the demo we are simulating the delay
    delay(2000)

    // return processed image
    onProcessingComplete(bitmap)
}

